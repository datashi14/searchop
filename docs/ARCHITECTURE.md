# SearchOp Architecture

## System Overview

SearchOp is a production-ready MLOps system for e-commerce search ranking. It implements a complete pipeline from data ingestion to deployed ranking service.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Data Layer                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Catalog    │    │  Clickstream │    │   Synthetic  │      │
│  │   (CSV)      │    │   Events     │    │   Generator  │      │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
│         │                    │                    │              │
│         └────────────────────┴────────────────────┘              │
│                            │                                      │
│                            ▼                                      │
│                  ┌─────────────────┐                             │
│                  │ Feature Store   │                             │
│                  │  (Parquet)      │                             │
│                  └─────────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ML Pipeline Layer                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Feature    │    │    Model     │    │  Evaluation  │      │
│  │ Engineering  │───▶│   Training   │───▶│   & Metrics  │      │
│  │              │    │  (LightGBM)  │    │  (NDCG/MRR)  │      │
│  └──────────────┘    └──────┬───────┘    └──────────────┘      │
│                             │                                    │
│                             ▼                                    │
│                  ┌─────────────────┐                             │
│                  │  Model Registry│                             │
│                  │  (Versioned)   │                             │
│                  └─────────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Serving Layer                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              FastAPI Ranking Service                      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │   │
│  │  │  /rank   │  │ /health  │  │ /metrics │              │   │
│  │  └──────────┘  └──────────┘  └──────────┘              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            │                                      │
│                            ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Prometheus Metrics                            │   │
│  │  - request_latency_seconds                                │   │
│  │  - requests_total                                         │   │
│  │  - rank_endpoint_errors_total                             │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Docker     │    │ Kubernetes   │    │   Terraform  │      │
│  │  Container   │───▶│  Deployment  │◀───│  (AWS EKS)   │      │
│  │              │    │  + HPA       │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  MLOps & Automation                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Dagster    │    │   CI/CD      │    │   Testing     │      │
│  │   Pipeline   │    │  (GitHub)    │    │  (4-Layer)   │      │
│  │  (Weekly)    │    │              │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Data Pipeline

**Inputs:**
- Product catalog (CSV/Parquet)
- Clickstream events (CSV/Parquet)
- Synthetic data generator for demos

**Processing:**
- Feature engineering: CTR, purchase rates, recency, popularity
- Query-product features: relevance scores, TF-IDF similarity
- Feature store: Parquet format for efficient access

**Output:**
- `data/processed/feature_store.parquet`

### 2. Model Training

**Algorithm:** LightGBM (Gradient Boosting)

**Features:**
- Product-level: CTR, ATC rate, purchase rate, recency, popularity
- Query-product: query CTR, query purchase rate, TF-IDF similarity
- Metadata: price, rating

**Training:**
- Train/validation split (80/20)
- Early stopping
- Model versioning (v1, v2, ...)

**Output:**
- `models/model_v{version}.pkl`
- Training metrics (AUC, log loss)

### 3. Inference Service

**Framework:** FastAPI

**Endpoints:**
- `POST /rank` - Rank products by query
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

**Flow:**
1. Receive query + candidate products
2. Lookup features from feature store
3. Load model from registry
4. Generate scores
5. Return ranked products

**Performance:**
- Target latency: <50ms (P95)
- Supports concurrent requests
- Health checks and readiness probes

### 4. Model Registry

**Storage:**
- Local filesystem: `models/model_v{version}.pkl`
- Version tracking: `models/current_model_version.txt`
- Metadata: `artifacts/training_metrics_{version}.json`

**Versioning:**
- Automatic version increment
- Current version pointer
- Historical metrics tracking

**Production:** Can be extended to S3, MLflow, or other registries

### 5. Feature Store

**Format:** Parquet

**Structure:**
- Query-product pairs as primary key
- Pre-computed features
- Efficient columnar storage

**Access:**
- Offline: Direct Parquet reads
- Online: Loaded into memory for API

**Production:** Can be extended to Redis, Feast, or Tecton

### 6. Evaluation Framework

**Metrics:**
- NDCG@10 (Normalized Discounted Cumulative Gain)
- MRR (Mean Reciprocal Rank)
- CTR@10 (Click-Through Rate)

**Process:**
1. Load evaluation dataset
2. Generate rankings for queries
3. Compute metrics vs ground truth
4. Compare to baseline
5. Enforce thresholds (gates)

**Thresholds:**
- NDCG@10 ≥ 0.25
- MRR ≥ 0.20
- CTR@10 ≥ 0.10
- Max 10% regression from baseline

### 7. Observability

**Prometheus Metrics:**
- `rank_requests_total` - Request counter
- `rank_request_duration_seconds` - Latency histogram
- `rank_endpoint_errors_total` - Error counter
- `model_version_info` - Current model version

**Logging:**
- Structured logging with levels
- Request/response logging
- Error tracking

**Health Checks:**
- Liveness probe: `/health`
- Readiness probe: `/health`
- Model availability check

### 8. Infrastructure

**Containerization:**
- Dockerfile with multi-stage build
- Health checks
- Optimized for production

**Kubernetes:**
- Deployment with resource limits
- Service (ClusterIP + Ingress)
- HPA (2-10 replicas, CPU/memory based)
- PersistentVolumeClaims for models/data

**Cloud:**
- Terraform for AWS EKS
- VPC, subnets, security groups
- S3 for model storage
- ECR for Docker images

### 9. MLOps Pipeline

**Orchestration:** Dagster

**Pipeline Steps:**
1. `ingest_data` - Generate/ingest new data
2. `build_feature_store` - Compute features
3. `train_ranking_model` - Train model
4. `evaluate_ranking_model` - Evaluate and gate

**Schedule:** Weekly (Sundays at 2 AM)

**Model Promotion:**
- Compare new vs current metrics
- Promote if improvement > 5%
- Update current version pointer

### 10. CI/CD

**GitHub Actions:**
- Linting (ruff, mypy)
- Unit tests
- Integration tests
- Model evaluation (on main)
- E2E tests (on main)

**Gates:**
- All tests must pass
- Metrics must meet thresholds
- No regression allowed

## Data Flow

```
User Query
    │
    ▼
FastAPI /rank endpoint
    │
    ├─▶ Load model from registry
    ├─▶ Lookup features from feature store
    ├─▶ Generate scores
    └─▶ Return ranked products
```

## Training Flow

```
Raw Data (Catalog + Events)
    │
    ▼
Feature Engineering
    │
    ▼
Feature Store (Parquet)
    │
    ▼
Model Training (LightGBM)
    │
    ├─▶ Model Registry
    ├─▶ Evaluation
    └─▶ Metrics Validation
```

## Deployment Flow

```
Code Commit
    │
    ▼
CI/CD Pipeline
    │
    ├─▶ Tests
    ├─▶ Build Docker Image
    └─▶ Deploy to K8s
    │
    ▼
Kubernetes Cluster
    │
    ├─▶ Deployment (2+ replicas)
    ├─▶ Service (Load balancer)
    └─▶ HPA (Auto-scaling)
```

## Performance Characteristics

**Latency:**
- P50: <20ms
- P95: <50ms
- P99: <100ms

**Throughput:**
- 100+ requests/second per instance
- Scales horizontally with HPA

**Resource Usage:**
- Memory: ~512MB per instance
- CPU: ~250m per instance
- Scales based on load

## Scalability

**Horizontal Scaling:**
- HPA: 2-10 replicas
- Based on CPU (70%) and memory (80%)
- Fast scale-up, gradual scale-down

**Vertical Scaling:**
- Resource limits configurable
- Can increase per-instance capacity

**Data Scaling:**
- Feature store: Parquet (columnar, efficient)
- Model: LightGBM (fast inference)
- Can extend to distributed feature stores

## Security

**Current:**
- Health checks
- Resource limits
- Error handling

**Production Additions:**
- Authentication/authorization
- TLS/HTTPS
- Network policies
- Secrets management
- RBAC

## Monitoring & Alerting

**Current:**
- Prometheus metrics
- Health endpoints
- Structured logging

**Production Additions:**
- Grafana dashboards
- AlertManager rules
- Distributed tracing
- Cost monitoring

## Future Enhancements

- [ ] Real-time feature computation
- [ ] A/B testing framework
- [ ] Shadow mode deployment
- [ ] Data drift detection
- [ ] Multi-model ensemble
- [ ] GraphQL API
- [ ] gRPC endpoint
- [ ] Model explainability

