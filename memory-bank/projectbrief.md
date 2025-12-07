# Project Brief: AI Ranking & Recommendations for E-Commerce Search API

## Project Overview
Building a realistic AI search/MLOps pipeline for an e-commerce catalog that demonstrates:
- Data ingestion (catalog + clickstream)
- Feature engineering and feature store
- Model training (ranking/recommendation)
- Microservice deployment on Kubernetes
- CI/CD pipeline
- Monitoring and canary rollouts simulation

## Core Requirements

### Data Components
1. **Product Catalog**: id, title, description, price, category, tags, brand, rating
2. **Clickstream Events**: user_id, product_id, query, event_type (view/click/add_to_cart/purchase), timestamp

### ML Pipeline
1. **Feature Engineering**:
   - Product features: CTR, add-to-cart rate, purchase rate, recency, popularity
   - Query-product features: relevance scores, TF-IDF similarity
2. **Model Training**: LightGBM or Logistic Regression for click probability prediction
3. **Model Registry**: Versioned model storage (S3/minio or local /models/)

### API Service
- FastAPI service with `/rank` endpoint
- Input: query, products list, user_id
- Output: ranked products with scores
- Health checks and metrics endpoints

### Infrastructure
- Docker containerization
- Kubernetes Deployment + Service + HPA
- CI/CD via GitHub Actions
- Dagster pipeline for scheduled retraining
- Prometheus metrics + basic monitoring

## Tech Stack
- **Language**: Python (primary)
- **ML**: scikit-learn / LightGBM
- **API**: FastAPI
- **Orchestration**: Kubernetes (kind/minikube)
- **Pipelines**: Dagster
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana (basic)

## Success Criteria
- End-to-end pipeline from data to deployed model
- Realistic e-commerce ranking scenario
- Production-ready patterns (monitoring, CI/CD, versioning)
- Demonstrates MLOps best practices

