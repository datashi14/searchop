# SearchOp Architecture

## System Overview

SearchOp is a production-ready MLOps system for e-commerce search ranking. It implements a complete pipeline from data ingestion to deployed ranking service, demonstrating real-world patterns used in companies like Algolia.

**Key Characteristics:**
- **End-to-End Pipeline**: Data → Features → Model → API → Deployment
- **Production-Ready**: Tested, monitored, and deployable to cloud
- **Scalable**: Kubernetes with HPA, supports horizontal scaling
- **Observable**: Prometheus metrics, structured logging, health checks
- **Automated**: CI/CD, scheduled retraining, metric gates

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Data Ingestion Layer                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐ │
│  │  Product Catalog │    │ Clickstream      │    │  Synthetic Data   │ │
│  │  (CSV/Parquet)   │    │ Events (CSV)     │    │  Generator       │ │
│  │  - 2000 products │    │ - 100k events    │    │  (Realistic)     │ │
│  │  - 10 categories │    │ - 1000 users     │    │  - User segments │ │
│  │  - Metadata      │    │ - 60 days        │    │  - Query noise   │ │
│  └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘ │
│           │                       │                        │            │
│           └───────────────────────┴────────────────────────┘            │
│                                   │                                      │
│                                   ▼                                      │
│                    ┌──────────────────────────────────┐                 │
│                    │      Feature Engineering         │                 │
│                    │   (build_feature_store.py)       │                 │
│                    │                                  │                 │
│                    │  • Product features:             │                 │
│                    │    - CTR, ATC rate, purchase     │                 │
│                    │    - Recency (7d views/purchases)│                 │
│                    │    - Popularity score            │                 │
│                    │  • Query-product features:       │                 │
│                    │    - Query-specific CTR           │                 │
│                    │    - Query purchase rate         │                 │
│                    │    - TF-IDF similarity           │                 │
│                    └──────────────┬───────────────────┘                 │
│                                   │                                      │
│                                   ▼                                      │
│                    ┌──────────────────────────────────┐                 │
│                    │      Feature Store                │                 │
│                    │  (Parquet - 20k+ query-product    │                 │
│                    │   pairs, 25 features)             │                 │
│                    └──────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         ML Training & Evaluation                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              Model Training (train_ranking_model.py)             │  │
│  │                                                                  │  │
│  │  Algorithm: LightGBM (Gradient Boosting)                        │  │
│  │  Features: 11 numeric features                                  │  │
│  │  Split: 80/20 train/validation                                  │  │
│  │  Early stopping: 10 rounds                                      │  │
│  │  Output: model_v{version}.pkl                                   │  │
│  └───────────────────────┬──────────────────────────────────────────┘  │
│                          │                                               │
│                          ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │           Model Evaluation (evaluate_model.py)                  │  │
│  │                                                                  │  │
│  │  Metrics:                                                        │  │
│  │  • NDCG@10 (Normalized Discounted Cumulative Gain)              │  │
│  │  • MRR (Mean Reciprocal Rank)                                    │  │
│  │  • CTR@10 (Click-Through Rate)                                  │  │
│  │                                                                  │  │
│  │  Thresholds (Gates):                                             │  │
│  │  • NDCG@10 ≥ 0.25                                               │  │
│  │  • MRR ≥ 0.20                                                   │  │
│  │  • CTR@10 ≥ 0.10                                                │  │
│  │  • Max 10% regression from baseline                            │  │
│  └───────────────────────┬──────────────────────────────────────────┘  │
│                          │                                               │
│                          ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              Model Registry                                       │  │
│  │                                                                  │  │
│  │  • models/model_v1.pkl, model_v2.pkl, ...                      │  │
│  │  • models/current_model_version.txt (pointer)                  │  │
│  │  • artifacts/training_metrics_{version}.json                   │  │
│  │  • artifacts/metrics.json (latest evaluation)                   │  │
│  │  • artifacts/baseline_metrics.json (for regression)            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Real-Time Inference Service                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              FastAPI Application (src/api/main.py)                │  │
│  │                                                                  │  │
│  │  Endpoints:                                                      │  │
│  │  • POST /rank      - Rank products by query                     │  │
│  │  • GET  /health    - Health check with model version            │  │
│  │  • GET  /metrics   - Prometheus metrics                         │  │
│  │  • GET  /docs      - Interactive API documentation              │  │
│  │                                                                  │  │
│  │  Request Flow:                                                   │  │
│  │  1. Receive query + candidate products                         │  │
│  │  2. Load model from registry (cached)                          │  │
│  │  3. Load feature store (cached or from disk)                  │  │
│  │  4. Lookup/compute features for query-product pairs            │  │
│  │  5. Generate scores using LightGBM model                      │  │
│  │  6. Sort products by score (descending)                        │  │
│  │  7. Return ranked products with scores                          │  │
│  │                                                                  │  │
│  │  Performance:                                                    │  │
│  │  • P50 latency: <20ms                                           │  │
│  │  • P95 latency: <50ms (SLO)                                    │  │
│  │  • P99 latency: <100ms                                         │  │
│  │  • Throughput: 100+ req/s per instance                        │  │
│  └───────────────────────┬──────────────────────────────────────────┘  │
│                          │                                               │
│                          ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │           Observability (src/api/monitoring.py)                  │  │
│  │                                                                  │  │
│  │  Prometheus Metrics:                                             │  │
│  │  • rank_requests_total{status="success|error"}                  │  │
│  │  • rank_request_duration_seconds (histogram)                    │  │
│  │  • rank_active_requests (gauge)                                │  │
│  │  • model_version_info{version="v1"} (gauge)                     │  │
│  │                                                                  │  │
│  │  Logging:                                                        │  │
│  │  • Structured logging with levels                               │  │
│  │  • Request/response logging                                     │  │
│  │  • Error tracking with stack traces                             │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Infrastructure & Deployment                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │   Containerization│    │   Kubernetes     │    │   Cloud (AWS)    │  │
│  │                  │    │                  │    │                  │  │
│  │  Dockerfile.api  │───▶│  Deployment      │◀───│  Terraform      │  │
│  │  • Python 3.11   │    │  • 2+ replicas   │    │  • EKS cluster   │  │
│  │  • Health checks │    │  • Resource      │    │  • VPC + subnets │  │
│  │  • Models baked  │    │    limits        │    │  • S3 for models │  │
│  │  • Features      │    │  • Liveness/     │    │  • ECR for images│  │
│  │    baked in      │    │    readiness     │    │                  │  │
│  │                  │    │                  │    │                  │  │
│  │                  │    │  Service         │    │                  │  │
│  │                  │    │  • ClusterIP     │    │                  │  │
│  │                  │    │  • Ingress       │    │                  │  │
│  │                  │    │                  │    │                  │  │
│  │                  │    │  HPA             │    │                  │  │
│  │                  │    │  • 2-10 replicas  │    │                  │  │
│  │                  │    │  • CPU: 70%      │    │                  │  │
│  │                  │    │  • Memory: 80%   │    │                  │  │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    MLOps Automation & Quality                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │        Dagster Pipeline (src/pipelines/dagster_pipeline.py)     │  │
│  │                                                                  │  │
│  │  Schedule: Weekly (Sundays at 2 AM)                             │  │
│  │                                                                  │  │
│  │  Pipeline Steps:                                                │  │
│  │  1. ingest_data()                                               │  │
│  │     → Generate/ingest new catalog + events                     │  │
│  │                                                                  │  │
│  │  2. build_feature_store(data)                                   │  │
│  │     → Compute features from raw data                           │  │
│  │                                                                  │  │
│  │  3. train_ranking_model(features)                                │  │
│  │     → Train LightGBM model                                      │  │
│  │     → Compare with current model                                │  │
│  │     → Promote if improvement > 5%                               │  │
│  │                                                                  │  │
│  │  4. evaluate_ranking_model(model)                               │  │
│  │     → Compute NDCG/MRR/CTR                                      │  │
│  │     → Check metric thresholds                                   │  │
│  │     → Fail if metrics below gates                               │  │
│  └───────────────────────┬──────────────────────────────────────────┘  │
│                          │                                               │
│                          ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │     CI/CD Pipeline (.github/workflows/ci.yml)                    │  │
│  │                                                                  │  │
│  │  Jobs:                                                           │  │
│  │  • Lint & Type Check (ruff, mypy)                               │  │
│  │  • Unit Tests (pytest tests/unit)                                │  │
│  │  • Integration Tests (pytest tests/integration)                  │  │
│  │  • Model Evaluation (on main branch)                            │  │
│  │  • E2E Tests (on main branch)                                   │  │
│  │                                                                  │  │
│  │  Gates:                                                          │  │
│  │  • All tests must pass                                           │  │
│  │  • Metrics must meet thresholds                                 │  │
│  │  • No regression allowed                                         │  │
│  └───────────────────────┬──────────────────────────────────────────┘  │
│                          │                                               │
│                          ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │      Testing Pyramid (tests/)                                   │  │
│  │                                                                  │  │
│  │  Layer 1: Unit Tests (10 tests)                                 │  │
│  │  • Config validation                                            │  │
│  │  • Feature functions                                            │  │
│  │  • API contracts                                                │  │
│  │                                                                  │  │
│  │  Layer 2: Integration Tests (6 tests)                           │  │
│  │  • Data schema validation                                       │  │
│  │  • Pipeline invariants                                          │  │
│  │                                                                  │  │
│  │  Layer 3: Model Tests (6 tests)                                 │  │
│  │  • Metric gates (NDCG/MRR/CTR)                                 │  │
│  │  • Regression detection                                         │  │
│  │                                                                  │  │
│  │  Layer 4: E2E Tests (6 tests)                                   │  │
│  │  • API smoke tests                                              │  │
│  │  • Latency SLO                                                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Detailed Component Architecture

### 1. Data Pipeline

**Location:** `src/data_ingestion/`

#### Data Generation (`generate_synthetic_data.py` / `scripts/generate_demo_data.py`)

**Input:** Configuration (number of products, events, users)

**Process:**
- Generates realistic product catalog with:
  - 2000 products across 10 categories
  - Realistic price distributions
  - Brand associations
  - Ratings (beta distribution, skewed high)
  - Stock status and popularity scores
- Generates clickstream events with:
  - 100k events for 1000 users over 60 days
  - User segments (high/medium/low activity)
  - Realistic event funnel (view → click → add_to_cart → purchase)
  - Query variations and typos
  - Time-based distribution (more recent = more events)

**Output:**
- `data/raw/catalog.csv` (189KB)
- `data/raw/events.csv` (3.7MB)

#### Feature Engineering (`build_feature_store.py`)

**Input:** Catalog + Events CSVs

**Process:**
1. **Product-Level Features:**
   - Aggregate events by product_id
   - Compute CTR = clicks / views
   - Compute ATC rate = add_to_cart / views
   - Compute purchase rate = purchases / views
   - Recent views/purchases (7-day window)
   - Popularity = normalized total views

2. **Query-Product Features:**
   - Aggregate by (query, product_id) pairs
   - Query-specific CTR and purchase rates
   - TF-IDF similarity between query and product title

3. **Feature Store Creation:**
   - Combine all features into single DataFrame
   - Key: (query, product_id)
   - 25 features total
   - Save as Parquet for efficient access

**Output:**
- `data/processed/feature_store.parquet` (394KB, 20k+ rows)

**Key Functions:**
- `compute_product_features()` - Product aggregations
- `compute_query_product_features()` - Query-product aggregations
- `compute_tfidf_similarity()` - Text similarity

### 2. Model Training

**Location:** `src/models/train_ranking_model.py`

#### Training Process

**Input:** Feature store Parquet

**Steps:**
1. **Feature Preparation:**
   - Select 11 numeric features:
     - `ctr`, `atc_rate`, `purchase_rate`
     - `recent_views_7d`, `recent_purchases_7d`, `popularity`
     - `query_ctr`, `query_purchase_rate`, `tfidf_similarity`
     - `price`, `rating`
   - Create binary label: `query_ctr > 0.1 OR query_purchase_rate > 0.05`

2. **Data Splitting:**
   - 80/20 train/validation split
   - Stratified by label to maintain class balance

3. **Model Training:**
   - Algorithm: LightGBM (Gradient Boosting)
   - Parameters:
     - `objective: "binary"`
     - `num_leaves: 31`
     - `learning_rate: 0.05`
     - Early stopping: 10 rounds
   - Training: 100 boosting rounds max

4. **Evaluation:**
   - Compute AUC (Area Under ROC Curve)
   - Compute log loss
   - On both train and validation sets

5. **Model Registry:**
   - Save model as `models/model_v{version}.pkl`
   - Version auto-increments (v1, v2, v3, ...)
   - Update `models/current_model_version.txt`
   - Save metrics to `artifacts/training_metrics_{version}.json`

**Output:**
- Trained LightGBM model (typically AUC > 0.95 on synthetic data)
- Training metrics (AUC, log loss)
- Model version tracking

### 3. Model Inference

**Location:** `src/models/inference.py`

#### Inference Flow

**Input:** Query + list of candidate products

**Process:**
1. **Feature Lookup:**
   - Load feature store from Parquet
   - For each candidate product:
     - Lookup features for (query, product_id) pair
     - If not found, use product-level features + compute TF-IDF on-the-fly
     - Fill missing features with defaults (0.0)

2. **Model Loading:**
   - Load current model from registry
   - Extract feature columns from model metadata
   - Cache model in memory (in production)

3. **Scoring:**
   - Prepare feature matrix for all candidates
   - Call `model.predict()` to get scores
   - Scores are probabilities (0-1 range)

4. **Ranking:**
   - Sort products by score (descending)
   - Return top-k or all products

**Output:** Ranked list of products with scores

**Key Functions:**
- `load_model()` - Load from registry with versioning
- `load_feature_store()` - Load Parquet feature store
- `prepare_features_for_ranking()` - Feature lookup/computation
- `rank_products()` - End-to-end ranking

### 4. API Service

**Location:** `src/api/`

#### FastAPI Application (`main.py`)

**Framework:** FastAPI with uvicorn ASGI server

**Structure:**
- Main app with lifespan management
- Router for ranking endpoint (`router_rank.py`)
- Schemas for request/response validation (`schemas.py`)
- Prometheus metrics integration (`monitoring.py`)

**Endpoints:**

**POST /rank**
- **Request:**
  ```json
  {
    "query": "running shoes",
    "user_id": "u-123",
    "products": [
      {
        "id": 1,
        "title": "Nike Running Shoes",
        "price": 99.99,
        "category": "sports_outdoors"
      }
    ]
  }
  ```
- **Response:**
  ```json
  {
    "ranked_products": [
      {
        "id": 1,
        "score": 0.95,
        "title": "Nike Running Shoes"
      }
    ],
    "query": "running shoes",
    "num_products": 1
  }
  ```
- **Flow:**
  1. Validate request (Pydantic)
  2. Load model and feature store
  3. Rank products
  4. Track metrics (latency, success/error)
  5. Return ranked results

**GET /health**
- Returns service status and model version
- Used by Kubernetes liveness/readiness probes

**GET /metrics**
- Prometheus-formatted metrics
- Exposed for scraping by Prometheus server

**GET /docs**
- Interactive Swagger UI
- Auto-generated from FastAPI schemas

#### Monitoring (`monitoring.py`)

**Prometheus Metrics:**
- `rank_requests_total{status="success|error"}` - Counter
- `rank_request_duration_seconds` - Histogram (buckets: 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
- `rank_active_requests` - Gauge
- `model_version_info{version="v1"}` - Gauge

**Integration:**
- Metrics exposed at `/metrics` endpoint
- Can be scraped by Prometheus
- Ready for Grafana dashboards

### 5. Model Registry

**Location:** `models/`

**Structure:**
```
models/
├── model_v1.pkl          # Versioned model files
├── model_v2.pkl
├── current_model_version.txt  # Pointer to current version
└── .gitkeep
```

**Versioning Strategy:**
- Automatic version increment: v1 → v2 → v3
- Current version tracked in `current_model_version.txt`
- Each model includes:
  - Trained LightGBM model
  - Feature columns used
  - Version metadata

**Metadata:**
- `artifacts/training_metrics_{version}.json` - Training metrics
- `artifacts/metrics.json` - Latest evaluation metrics
- `artifacts/baseline_metrics.json` - Baseline for regression detection

**Production Extension:**
- Can be extended to S3, MLflow, or other registries
- Current implementation uses local filesystem (works for Docker/K8s)

### 6. Feature Store

**Location:** `data/processed/feature_store.parquet`

**Format:** Apache Parquet (columnar storage)

**Structure:**
- Primary key: (query, product_id)
- 25 features total:
  - Identifiers: query, product_id, title, category
  - Product features: ctr, atc_rate, purchase_rate, recent_views_7d, recent_purchases_7d, popularity
  - Query-product features: query_ctr, query_purchase_rate, tfidf_similarity
  - Metadata: price, rating, brand, tags

**Access Patterns:**
- **Offline:** Direct Parquet reads for training
- **Online:** Loaded into memory for API (or cached in Redis)

**Size:** ~394KB for 20k+ query-product pairs

**Production Extension:**
- Can be extended to Redis for low-latency access
- Or Feast/Tecton for feature serving
- Current implementation: Parquet file (works for demo/production)

### 7. Evaluation Framework

**Location:** `src/models/evaluate_model.py`

#### Evaluation Process

**Input:**
- Trained model
- Feature store
- Evaluation dataset (auto-generated or provided)

**Metrics Computed:**

1. **NDCG@10** (Normalized Discounted Cumulative Gain)
   - Measures ranking quality
   - Accounts for position (top results weighted more)
   - Normalized by ideal ranking
   - Range: 0-1 (higher is better)

2. **MRR** (Mean Reciprocal Rank)
   - Average of 1/rank for first relevant item
   - Good for "did we put the right item near the top?"
   - Range: 0-1 (higher is better)

3. **CTR@10** (Click-Through Rate at top 10)
   - Percentage of top-10 results that would be clicked
   - Proxy for relevance
   - Range: 0-1 (higher is better)

**Process:**
1. Load evaluation dataset (queries + ground truth clicks)
2. For each query:
   - Get candidate products
   - Generate rankings using model
   - Compute metrics vs ground truth
3. Aggregate metrics across all queries
4. Compare to baseline
5. Enforce thresholds

**Thresholds (Gates):**
- NDCG@10 ≥ 0.25 (minimum acceptable)
- MRR ≥ 0.20 (minimum acceptable)
- CTR@10 ≥ 0.10 (minimum acceptable)
- Max 10% regression from baseline

**Output:**
- `artifacts/metrics.json` - Latest metrics
- `artifacts/baseline_metrics.json` - Baseline (created on first run)

### 8. Infrastructure

#### Docker Containerization

**Location:** `docker/Dockerfile.api`

**Base Image:** `python:3.11-slim`

**Layers:**
1. System dependencies (gcc for LightGBM)
2. Python dependencies (requirements.txt)
3. Application code (src/)
4. Models and data (baked into image)
5. Health check configuration

**Optimizations:**
- Multi-stage build (if needed)
- Layer caching
- Minimal base image
- Health checks

**Size:** ~500MB (with models and data)

#### Kubernetes Deployment

**Location:** `k8s/`

**Manifests:**

1. **Deployment** (`deployment-api.yaml`):
   - Replicas: 2 (minimum)
   - Resource requests: 512Mi memory, 250m CPU
   - Resource limits: 1Gi memory, 500m CPU
   - Liveness probe: `/health` every 10s
   - Readiness probe: `/health` every 5s
   - Environment variables for paths

2. **Service** (`service-api.yaml`):
   - Type: ClusterIP (internal)
   - Port: 80 → 8000 (container)
   - Optional: Ingress for external access

3. **HPA** (`hpa-api.yaml`):
   - Min replicas: 2
   - Max replicas: 10
   - CPU target: 70%
   - Memory target: 80%
   - Scale-up: Fast (0s stabilization)
   - Scale-down: Gradual (300s stabilization)

4. **PVCs** (in deployment):
   - Models PVC: 1Gi
   - Feature store PVC: 2Gi
   - Access mode: ReadWriteMany

#### Cloud Infrastructure (AWS)

**Location:** `infra/aws/`

**Terraform Modules:**

1. **VPC** (`terraform-aws-modules/vpc/aws`):
   - CIDR: 10.0.0.0/16
   - 2 AZs with public/private subnets
   - NAT gateway for private subnet internet access

2. **EKS Cluster** (`terraform-aws-modules/eks/aws`):
   - Kubernetes version: 1.28
   - Managed node group:
     - Instance type: t3.medium
     - Min: 2, Max: 10, Desired: 3
     - Capacity type: ON_DEMAND

3. **S3 Bucket**:
   - Name: `{project}-models-{env}`
   - Versioning enabled
   - For model storage (future)

4. **ECR Repository**:
   - Name: `{project}-api`
   - Image scanning on push
   - For Docker images

5. **IAM Roles**:
   - EKS node role with S3 read permissions
   - For accessing models from S3

### 9. MLOps Pipeline

**Location:** `src/pipelines/dagster_pipeline.py`

#### Dagster Pipeline

**Orchestration:** Dagster (Python-native)

**Pipeline Definition:**
```python
@job
def ranking_pipeline():
    data = ingest_data()
    features = build_feature_store(data)
    model = train_ranking_model(features)
    evaluation = evaluate_ranking_model(model)
    return evaluation
```

**Operations:**

1. **ingest_data()**
   - Calls `generate_synthetic_data.py`
   - Creates catalog and events CSVs
   - Materializes assets (catalog_data, events_data)

2. **build_feature_store(data)**
   - Calls `build_feature_store.py`
   - Computes features from raw data
   - Creates feature store Parquet
   - Materializes asset (feature_store)

3. **train_ranking_model(features)**
   - Calls `train_ranking_model.py`
   - Trains new model
   - Compares with current model
   - Promotes if improvement > 5% threshold
   - Materializes asset (ranking_model)

4. **evaluate_ranking_model(model)**
   - Calls `evaluate_model.py`
   - Computes NDCG/MRR/CTR
   - Checks metric thresholds
   - Materializes asset (model_evaluation)

**Schedule:**
- Weekly: Sundays at 2 AM
- Configurable via Dagster UI

**Model Promotion Logic:**
- Compare new model val_auc vs current model val_auc
- If improvement > 5%: promote (update current version)
- Otherwise: keep current model, log warning

### 10. CI/CD Pipeline

**Location:** `.github/workflows/ci.yml`

#### GitHub Actions Workflow

**Triggers:**
- Push to main/develop
- Pull requests to main/develop

**Jobs:**

1. **Lint & Type Check**
   - Runs: ruff, mypy
   - Fast feedback (< 1 min)
   - Blocks merge if fails

2. **Unit Tests**
   - Runs: `pytest tests/unit`
   - Fast tests (< 1 min)
   - No data dependencies

3. **Integration Tests**
   - Runs: `pytest tests/integration`
   - Requires: Generated data
   - Validates: Data schemas, invariants

4. **Model Evaluation** (conditional)
   - Runs on: main branch OR PR with `run-eval` label
   - Steps:
     1. Generate data
     2. Build features
     3. Train model
     4. Evaluate model
     5. Run metric gate tests
   - Blocks merge if metrics below thresholds

5. **E2E Tests** (conditional)
   - Runs on: main branch only
   - Steps:
     1. Generate data
     2. Build features
     3. Start API server
     4. Run E2E tests
   - Validates: API works end-to-end

**Gates:**
- All jobs must pass
- Metrics must meet thresholds
- No regression allowed

## Data Flows

### Real-Time Ranking Flow

```
User Request
    │
    ▼
POST /rank
    │
    ├─▶ Validate request (Pydantic)
    │
    ├─▶ Load model from registry
    │   └─▶ models/model_v{version}.pkl
    │
    ├─▶ Load feature store
    │   └─▶ data/processed/feature_store.parquet
    │
    ├─▶ For each candidate product:
    │   ├─▶ Lookup features (query, product_id)
    │   ├─▶ Compute missing features (TF-IDF, defaults)
    │   └─▶ Build feature vector
    │
    ├─▶ Model.predict(feature_matrix)
    │   └─▶ Generate scores (0-1)
    │
    ├─▶ Sort by score (descending)
    │
    ├─▶ Track metrics (latency, success)
    │
    └─▶ Return ranked products
```

### Training Flow

```
Raw Data (Catalog + Events)
    │
    ▼
Feature Engineering
    ├─▶ Product aggregations
    ├─▶ Query-product aggregations
    └─▶ TF-IDF computation
    │
    ▼
Feature Store (Parquet)
    │
    ▼
Prepare Training Data
    ├─▶ Select 11 numeric features
    ├─▶ Create binary labels
    └─▶ Train/validation split (80/20)
    │
    ▼
Train LightGBM
    ├─▶ 100 boosting rounds
    ├─▶ Early stopping (10 rounds)
    └─▶ Validation monitoring
    │
    ▼
Evaluate Model
    ├─▶ Compute AUC, log loss
    └─▶ Save metrics
    │
    ▼
Model Registry
    ├─▶ Save model_v{version}.pkl
    ├─▶ Update current_model_version.txt
    └─▶ Save training_metrics_{version}.json
```

### MLOps Pipeline Flow

```
Weekly Schedule (Sunday 2 AM)
    │
    ▼
Dagster Pipeline Triggered
    │
    ├─▶ ingest_data()
    │   └─▶ Generate new catalog + events
    │
    ├─▶ build_feature_store(data)
    │   └─▶ Compute features → feature_store.parquet
    │
    ├─▶ train_ranking_model(features)
    │   ├─▶ Train new model
    │   ├─▶ Compare with current
    │   └─▶ Promote if improvement > 5%
    │
    └─▶ evaluate_ranking_model(model)
        ├─▶ Compute NDCG/MRR/CTR
        ├─▶ Check thresholds
        └─▶ Fail if below gates
```

### Deployment Flow

```
Code Commit
    │
    ▼
GitHub Actions Triggered
    │
    ├─▶ Lint & Type Check
    ├─▶ Unit Tests
    ├─▶ Integration Tests
    ├─▶ Model Evaluation (if on main)
    └─▶ E2E Tests (if on main)
    │
    ▼
All Tests Pass
    │
    ▼
Build Docker Image
    ├─▶ docker build -f docker/Dockerfile.api
    └─▶ Tag with version
    │
    ▼
Push to ECR (if configured)
    └─▶ docker push {ecr_url}:{tag}
    │
    ▼
Deploy to Kubernetes
    ├─▶ kubectl apply -f k8s/deployment-api.yaml
    ├─▶ kubectl apply -f k8s/service-api.yaml
    └─▶ HPA automatically scales
```

## Performance Characteristics

### Latency

**Measured on:** Local machine, EKS deployment

**Results:**
- P50: <20ms
- P95: <50ms (meets SLO)
- P99: <100ms
- Max: <200ms (under load)

**Factors:**
- Model inference: ~5-10ms
- Feature lookup: ~5-15ms
- Serialization: ~1-2ms
- Network: Variable

### Throughput

**Per Instance:**
- 100+ requests/second
- Scales linearly with replicas

**With HPA (10 replicas):**
- 1000+ requests/second total
- Auto-scales based on CPU/memory

### Resource Usage

**Per Pod:**
- Memory: ~512MB (request) to 1Gi (limit)
- CPU: ~250m (request) to 500m (limit)

**Cluster (3 nodes, 2 pods each):**
- Total memory: ~3Gi
- Total CPU: ~1.5 cores

## Scalability

### Horizontal Scaling

**HPA Configuration:**
- Min: 2 replicas
- Max: 10 replicas
- Scale on: CPU (70%) and memory (80%)

**Behavior:**
- Scale-up: Fast (0s stabilization, 100% increase or +2 pods)
- Scale-down: Gradual (300s stabilization, 50% decrease)

**Tested:** Successfully scales from 2 to 10 replicas under load

### Vertical Scaling

**Resource Limits:**
- Configurable in `k8s/deployment-api.yaml`
- Can increase per-instance capacity
- Trade-off: Fewer instances vs more capacity per instance

### Data Scaling

**Feature Store:**
- Current: 20k+ query-product pairs (~394KB)
- Parquet format: Efficient for millions of rows
- Can extend to distributed storage (S3, HDFS)

**Model:**
- LightGBM: Fast inference, small model size
- Model size: ~1-5MB typically
- Can handle 1000+ features

## Security

### Current Implementation

- **Health Checks:** Liveness and readiness probes
- **Resource Limits:** Prevent resource exhaustion
- **Error Handling:** Graceful degradation
- **Logging:** Structured, no sensitive data

### Production Additions

- **Authentication:** API keys, OAuth, JWT
- **Authorization:** Role-based access control
- **TLS/HTTPS:** Encrypted communication
- **Network Policies:** Pod-to-pod communication rules
- **Secrets Management:** AWS Secrets Manager, K8s secrets
- **RBAC:** Kubernetes role-based access control
- **Image Scanning:** ECR automatic scanning
- **VPC:** Private subnets for pods

## Monitoring & Observability

### Prometheus Metrics

**Exposed at:** `/metrics`

**Metrics:**
- `rank_requests_total{status="success|error"}` - Request counter
- `rank_request_duration_seconds` - Latency histogram
- `rank_active_requests` - Active request gauge
- `model_version_info{version="v1"}` - Model version

**Integration:**
- Can be scraped by Prometheus server
- Ready for Grafana dashboards
- AlertManager rules can be configured

### Logging

**Format:** Structured JSON (configurable)

**Levels:** DEBUG, INFO, WARNING, ERROR

**Content:**
- Request/response logging
- Error stack traces
- Model version info
- Performance metrics

**Destination:**
- stdout/stderr (container logs)
- Can be collected by Fluentd/Fluent Bit
- Can be sent to CloudWatch, Stackdriver, etc.

### Health Checks

**Endpoint:** `/health`

**Response:**
```json
{
  "status": "healthy",
  "version": "v1"
}
```

**Used by:**
- Kubernetes liveness probe
- Kubernetes readiness probe
- Load balancer health checks

## Testing Strategy

### 4-Layer Testing Pyramid

**Layer 1: Unit Tests** (10 tests)
- Location: `tests/unit/`
- Speed: < 1s each
- Coverage: Config, feature functions, API contracts
- No dependencies: Pure code logic

**Layer 2: Integration Tests** (6 tests)
- Location: `tests/integration/`
- Speed: < 2s each
- Coverage: Data schemas, pipeline invariants
- Dependencies: Generated data files

**Layer 3: Model Tests** (6 tests)
- Location: `tests/model/`
- Speed: < 5s each
- Coverage: Metric gates, regression detection
- Dependencies: Trained model, evaluation metrics

**Layer 4: E2E Tests** (6 tests)
- Location: `tests/e2e/`
- Speed: < 10s each
- Coverage: API smoke tests, latency SLO
- Dependencies: Running API service

**Total:** 28+ tests, all passing ✅

## Deployment Status

### Successfully Deployed To

- ✅ **Local Development** - Docker, uvicorn
- ✅ **Local Kubernetes** - kind cluster
- ✅ **AWS EKS** - ap-southeast-2 region
- ✅ **GitHub Actions** - CI/CD pipeline

### Deployment Time

- **Local:** < 5 minutes
- **Local K8s:** < 10 minutes
- **AWS EKS:** ~30 minutes (first time)
- **Redeploy:** ~5 minutes

## Technology Stack

### Core
- **Python 3.11+** - Primary language
- **FastAPI** - Web framework
- **LightGBM** - ML model
- **Pandas** - Data processing
- **NumPy** - Numerical computing

### Infrastructure
- **Docker** - Containerization
- **Kubernetes** - Orchestration
- **Terraform** - Infrastructure as code
- **AWS EKS** - Managed Kubernetes

### MLOps
- **Dagster** - Pipeline orchestration
- **Prometheus** - Metrics
- **GitHub Actions** - CI/CD

### Data
- **Parquet** - Feature store format
- **CSV** - Raw data format
- **Pickle** - Model serialization

## Future Enhancements

### Short Term
- [ ] Real-time feature computation
- [ ] Redis caching for features
- [ ] Model explainability (SHAP)
- [ ] A/B testing framework

### Medium Term
- [ ] Shadow mode deployment
- [ ] Data drift detection
- [ ] Multi-model ensemble
- [ ] GraphQL API
- [ ] gRPC endpoint

### Long Term
- [ ] Distributed feature store (Feast/Tecton)
- [ ] Real-time streaming (Kafka)
- [ ] Advanced NLP features (embeddings)
- [ ] Reinforcement learning for ranking
- [ ] Multi-region deployment

## Architecture Decisions

### Why LightGBM?
- Fast inference (<10ms)
- Handles mixed feature types
- Good for ranking problems
- Small model size
- Production-tested

### Why FastAPI?
- High performance (async)
- Automatic API docs
- Type validation (Pydantic)
- Easy to test
- Production-ready

### Why Parquet for Feature Store?
- Columnar format (efficient)
- Fast reads
- Compression
- Schema evolution
- Industry standard

### Why Kubernetes?
- Industry standard
- Auto-scaling
- Self-healing
- Multi-cloud
- Production-ready

### Why Dagster?
- Python-native
- Great DX
- Asset tracking
- Easy testing
- Modern alternative to Airflow

## Conclusion

SearchOp demonstrates a **complete, production-ready MLOps system** that:

- ✅ Runs end-to-end (data → model → API)
- ✅ Deploys to cloud (AWS EKS)
- ✅ Monitors and observes (Prometheus)
- ✅ Tests comprehensively (4-layer pyramid)
- ✅ Automates retraining (Dagster)
- ✅ Enforces quality (CI/CD gates)

This architecture is suitable for:
- E-commerce search ranking
- Recommendation systems
- Content ranking
- Any learning-to-rank problem

The system is **not theoretical** - it's been deployed, tested, and verified on real infrastructure.
