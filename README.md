# SearchOp: AI Ranking & Recommendations for E-Commerce Search API

A realistic AI search/MLOps pipeline for an e-commerce catalog demonstrating end-to-end ML production patterns.

## Overview

This project implements:
- **Data Ingestion**: Synthetic product catalog and clickstream events
- **Feature Engineering**: Product and query-product feature computation
- **Model Training**: LightGBM-based ranking model
- **API Service**: FastAPI microservice for real-time ranking
- **MLOps Pipeline**: Dagster-based scheduled retraining
- **Infrastructure**: Kubernetes deployment with HPA
- **CI/CD**: GitHub Actions pipeline

## Project Structure

```
searchop/
├── README.md
├── pyproject.toml
├── requirements.txt
├── src/
│   ├── data_ingestion/
│   │   ├── generate_synthetic_data.py
│   │   └── build_feature_store.py
│   ├── models/
│   │   ├── train_ranking_model.py
│   │   └── inference.py
│   ├── api/
│   │   ├── main.py
│   │   ├── schemas.py
│   │   ├── router_rank.py
│   │   └── monitoring.py
│   ├── pipelines/
│   │   └── dagster_pipeline.py
│   └── utils/
│       ├── config.py
│       └── logging_utils.py
├── models/
│   └── .gitkeep
├── data/
│   ├── raw/
│   └── processed/
├── docker/
│   └── Dockerfile.api
├── k8s/
│   ├── deployment-api.yaml
│   ├── service-api.yaml
│   └── hpa-api.yaml
├── .github/
│   └── workflows/
│       └── ci_cd.yaml
└── tests/
    ├── test_inference.py
    └── test_api.py
```

## Quick Start

### 1. Setup Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Generate Synthetic Data

```bash
python src/data_ingestion/generate_synthetic_data.py
```

This creates:
- `data/raw/catalog.csv`: Product catalog
- `data/raw/events.csv`: Clickstream events

### 3. Build Feature Store

```bash
python src/data_ingestion/build_feature_store.py
```

Generates `data/processed/feature_store.parquet`

### 4. Train Model

```bash
python src/models/train_ranking_model.py
```

Saves model to `models/model_v1.pkl`

### 5. Run API Service

```bash
uvicorn src.api.main:app --reload
```

API available at `http://localhost:8000`

### 6. Test Ranking Endpoint

```bash
curl -X POST "http://localhost:8000/rank" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "running shoes",
    "user_id": "u-1",
    "products": [
      {"id": 1, "title": "Nike Running Shoes", "price": 99.99, "category": "footwear"}
    ]
  }'
```

## API Endpoints

- `GET /health`: Health check
- `GET /metrics`: Prometheus metrics
- `POST /rank`: Rank products by query

## Deployment

### Docker

```bash
docker build -f docker/Dockerfile.api -t searchop-api .
docker run -p 8000:8000 searchop-api
```

### Kubernetes

```bash
kubectl apply -f k8s/
```

## MLOps Pipeline

Run Dagster pipeline:

```bash
dagster dev
```

Access Dagster UI at `http://localhost:3000`

## CI/CD

GitHub Actions workflow automatically:
- Runs tests
- Lints code
- Builds Docker image
- Deploys to Kubernetes (if configured)

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
PYTHONPATH=. python src/data_ingestion/generate_synthetic_data.py
PYTHONPATH=. python src/data_ingestion/build_feature_store.py
PYTHONPATH=. python src/models/train_ranking_model.py
PYTHONPATH=. python src/models/evaluate_model.py
pytest tests/ -v
```

## CI/CD

GitHub Actions workflow enforces:
- Code linting (ruff, mypy)
- Unit and integration tests
- Model metric gates (NDCG@10, MRR, CTR thresholds)
- Regression detection (max 10% performance drop)

**No PR can be merged unless all tests pass and metrics meet thresholds.**

## Monitoring

- Prometheus metrics at `/metrics`
- Request latency, throughput, error rates
- Basic drift detection
- Offline model evaluation with hard thresholds

## License

MIT

