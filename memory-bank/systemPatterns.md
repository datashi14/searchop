# System Patterns

## Architecture Overview

```
Data Generation → Feature Engineering → Model Training → API Service
                                                          ↓
                                    Dagster Pipeline ← Model Registry
                                                          ↓
                                    CI/CD → Kubernetes Deployment
```

## Component Relationships

### Data Layer
- **Synthetic Data Generator**: Creates realistic catalog and clickstream data
- **Feature Store**: Parquet files with pre-computed features (product + query-product pairs)

### ML Layer
- **Training Script**: Loads features, trains model, saves versioned artifacts
- **Model Registry**: Simple file-based versioning (model_v1.pkl, model_v2.pkl)
- **Inference**: FastAPI service loads model and feature store for real-time ranking

### Infrastructure Layer
- **Docker**: Containerized API service
- **Kubernetes**: Deployment, Service, HPA for scaling
- **Dagster**: Scheduled pipeline for retraining
- **CI/CD**: GitHub Actions for automated testing and deployment

## Key Design Patterns

### Feature Engineering
- Product-level aggregations (CTR, rates, recency)
- Query-product pair features (historical relevance)
- NLP features (TF-IDF similarity)

### Model Serving
- Stateless API design
- Feature lookup from pre-computed store
- Real-time scoring with model inference

### MLOps Patterns
- Model versioning and promotion based on metrics
- Scheduled retraining pipeline
- Monitoring with Prometheus metrics
- Health checks and readiness probes

