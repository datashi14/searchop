# SearchOp: AI Ranking & Recommendations for E-Commerce Search API

A production-ready MLOps reference implementation for e-commerce search ranking. This project demonstrates end-to-end ML production patterns: data pipelines, feature engineering, model training, API serving, containerization, Kubernetes deployment, and automated retraining.

**Built for roles like Algolia's Senior AI/MLOps Engineer** - showcasing system design, operational expertise, and production-ready patterns.

## What This Demonstrates

- ✅ **System Design**: Complete MLOps pipeline from data to deployed model
- ✅ **Operational Expertise**: Docker, Kubernetes, monitoring, autoscaling
- ✅ **Production Patterns**: Testing, CI/CD, model versioning, feature stores
- ✅ **Real-World Readiness**: Can be deployed to AWS/GCP/Azure in hours

## Overview

This project implements:
- **Data Ingestion**: Realistic synthetic e-commerce data (catalog + clickstream)
- **Feature Engineering**: Product and query-product feature computation
- **Model Training**: LightGBM-based ranking model with versioning
- **API Service**: FastAPI microservice for real-time ranking
- **MLOps Pipeline**: Dagster-based scheduled retraining
- **Infrastructure**: Kubernetes deployment with HPA
- **Testing**: 4-layer testing pyramid with metric gates
- **CI/CD**: GitHub Actions pipeline

## Quick Start

### 1. Setup Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Generate Demo Data & Train Model

**Option A: One-command demo (recommended)**
```bash
make demo
```

**Option B: Step by step**
```bash
# Generate realistic demo data
make data

# Build feature store
make features

# Train model
make train

# Evaluate model
make evaluate
```

This creates:
- `data/raw/catalog.csv`: Product catalog (2000 products)
- `data/raw/events.csv`: Clickstream events (100k events)
- `data/processed/feature_store.parquet`: Feature store
- `models/model_v1.pkl`: Trained ranking model

### 3. Run API Service

```bash
make api
# or
uvicorn src.api.main:app --reload
```

API available at:
- Service: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics

### 4. Test Ranking Endpoint

```bash
curl -X POST "http://localhost:8000/rank" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "running shoes",
    "user_id": "u-1",
    "products": [
      {"id": 1, "title": "Nike Running Shoes", "price": 99.99, "category": "sports_outdoors"}
    ]
  }'
```

## Project Structure

```
searchop/
├── src/
│   ├── data_ingestion/     # Data pipeline
│   ├── models/             # Training & evaluation
│   ├── api/                # FastAPI service
│   ├── pipelines/          # Dagster pipeline
│   └── utils/              # Utilities
├── tests/                  # 4-layer test suite
├── scripts/                # Demo scripts
├── docker/                 # Containerization
├── k8s/                    # Kubernetes manifests
├── infra/                  # Infrastructure as code
│   ├── local-cluster/      # kind setup
│   └── aws/                # Terraform for EKS
└── docs/                   # Documentation
```

## API Endpoints

- `GET /health`: Health check
- `GET /metrics`: Prometheus metrics
- `POST /rank`: Rank products by query

## Deployment

### Local Development

```bash
# Start API server
make api
# or
uvicorn src.api.main:app --reload

# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Local Kubernetes (kind)

Deploy to a local Kubernetes cluster for testing:

```bash
# Setup cluster
make kind-setup

# Build and load image
make kind-load-image

# Deploy
make kind-deploy

# Port forward
kubectl port-forward -n searchop service/searchop-api 8000:80
```

See [docs/DEPLOY_LOCAL_K8S.md](docs/DEPLOY_LOCAL_K8S.md) for detailed instructions.

### Docker

```bash
# Build image
docker build -f docker/Dockerfile.api -t searchop-api:latest .

# Run container
docker run -p 8000:8000 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/data/processed:/app/data/processed \
  searchop-api:latest
```

### Cloud Deployment (AWS EKS)

The project includes Terraform configuration for AWS EKS deployment:

```bash
cd infra/aws
terraform init
terraform plan
terraform apply
```

See [docs/DEPLOY_AWS_EKS.md](docs/DEPLOY_AWS_EKS.md) for complete guide.

**Note**: The Terraform configuration is a reference implementation. It demonstrates production-ready infrastructure patterns but is not kept running to avoid costs. With AWS credentials, you can deploy it in a few hours.

## MLOps Pipeline

### Dagster Pipeline

The Dagster pipeline orchestrates:
1. Data ingestion
2. Feature engineering
3. Model training
4. Model evaluation

**Run locally**:
```bash
dagster dev
```

Access Dagster UI at `http://localhost:3000`

**Schedule**: Pipeline runs weekly (Sundays at 2 AM) via `weekly_retraining_schedule`

**Pipeline steps**:
- `ingest_data`: Generate/ingest new data
- `build_feature_store`: Compute features
- `train_ranking_model`: Train new model (promotes if improvement > 5%)
- `evaluate_ranking_model`: Evaluate and check metric thresholds

## Testing

This project implements a comprehensive 4-layer testing pyramid:

1. **Unit Tests**: Fast code tests (< 1s each)
2. **Integration Tests**: Data pipeline validation
3. **Model Evaluation**: Performance metric gates
4. **E2E Tests**: API smoke tests

See [docs/TESTING.md](docs/TESTING.md) for detailed testing guide.

### Quick Test Run

```bash
# Unit & integration tests
pytest tests/unit tests/integration -v

# Full suite (requires data and model)
make demo
pytest tests/ -v
```

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`) enforces:
- Code linting (ruff, mypy)
- Unit tests (fast code validation)
- Integration tests (data pipeline validation)
- Model evaluation (metric gates on main branch)
- E2E tests (API smoke tests)

**No PR can be merged unless all tests pass and metrics meet thresholds.**

## Monitoring

- Prometheus metrics at `/metrics`
- Request latency, throughput, error rates
- Basic drift detection
- Offline model evaluation with hard thresholds

## Documentation

- [Testing Guide](docs/TESTING.md) - Comprehensive testing strategy
- [MLOps Testing](docs/MLOPS_TESTING.md) - Testing philosophy for AI systems
- [Deployment Guide](docs/DEPLOYMENT.md) - Deployment instructions
- [Local K8s Deployment](docs/DEPLOY_LOCAL_K8S.md) - kind cluster setup
- [AWS EKS Deployment](docs/DEPLOY_AWS_EKS.md) - Cloud deployment guide

## About This Project

This is a **reference implementation** designed to demonstrate MLOps best practices. It's production-ready code that can be deployed to cloud infrastructure, but it's not kept running to avoid ongoing costs.

**What it shows:**
- Complete system design and architecture
- Production-ready patterns (monitoring, CI/CD, versioning)
- Operational expertise (Kubernetes, Docker, infrastructure)
- Quality assurance (comprehensive testing, metric gates)

**What it doesn't require:**
- Constantly-running cloud infrastructure
- Real customer data
- Ongoing maintenance costs

**For interviews:** This demonstrates that with access to AWS/GCP/Azure, you can deploy a production-ready MLOps system in hours, not weeks.

## License

MIT
