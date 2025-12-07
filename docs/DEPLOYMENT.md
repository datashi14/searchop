# Deployment Guide

## Overview

This guide covers deploying SearchOp to various environments:
- Local development
- Docker
- Kubernetes
- Cloud platforms (AWS/GCP/Azure)

## Prerequisites

- Python 3.11+
- Docker (for containerized deployment)
- Kubernetes cluster (for K8s deployment)
- Models and feature store data

## Local Development

### 1. Setup Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Generate Data & Train Model

```bash
# Generate synthetic data
PYTHONPATH=. python src/data_ingestion/generate_synthetic_data.py

# Build feature store
PYTHONPATH=. python src/data_ingestion/build_feature_store.py

# Train model
PYTHONPATH=. python src/models/train_ranking_model.py

# Evaluate model
PYTHONPATH=. python src/models/evaluate_model.py
```

### 3. Run API

```bash
uvicorn src.api.main:app --reload
```

API available at:
- Service: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics

## Docker Deployment

### Build Image

```bash
docker build -f docker/Dockerfile.api -t searchop-api:latest .
```

### Run Container

```bash
docker run -d \
  --name searchop-api \
  -p 8000:8000 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/data/processed:/app/data/processed \
  searchop-api:latest
```

### Docker Compose (Optional)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    ports:
      - "8000:8000"
    volumes:
      - ./models:/app/models
      - ./data/processed:/app/data/processed
    environment:
      - PYTHONPATH=/app
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Run:
```bash
docker-compose up -d
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (minikube, kind, or cloud)
- kubectl configured
- Models and feature store accessible

### 1. Prepare Data Volumes

**Option A: Use PersistentVolumes**

```bash
# Create PVCs (included in k8s/deployment-api.yaml)
kubectl apply -f k8s/deployment-api.yaml
```

**Option B: Use ConfigMaps/Secrets for small data**

```bash
# Create ConfigMap for feature store (if small enough)
kubectl create configmap feature-store \
  --from-file=data/processed/feature_store.parquet
```

### 2. Build and Push Image

```bash
# Build
docker build -f docker/Dockerfile.api -t searchop-api:latest .

# Tag for registry
docker tag searchop-api:latest your-registry/searchop-api:latest

# Push
docker push your-registry/searchop-api:latest
```

### 3. Update Deployment

Edit `k8s/deployment-api.yaml` to use your image:

```yaml
image: your-registry/searchop-api:latest
```

### 4. Deploy

```bash
# Deploy all resources
kubectl apply -f k8s/

# Or use kustomize
kubectl apply -k k8s/

# Check status
kubectl get pods -l app=searchop-api
kubectl get services
kubectl get hpa
```

### 5. Access Service

**ClusterIP (internal)**:
```bash
kubectl port-forward service/searchop-api 8000:80
```

**Ingress (external)**:
- Configure ingress controller
- Update `k8s/service-api.yaml` ingress host
- Access via configured domain

### 6. Monitor

```bash
# View logs
kubectl logs -l app=searchop-api -f

# Check metrics
kubectl port-forward service/searchop-api 8000:80
curl http://localhost:8000/metrics

# HPA status
kubectl get hpa searchop-api-hpa
```

## Horizontal Pod Autoscaling (HPA)

HPA is configured in `k8s/hpa-api.yaml`:

- **Min replicas**: 2
- **Max replicas**: 10
- **CPU target**: 70%
- **Memory target**: 80%

Monitor scaling:
```bash
kubectl get hpa searchop-api-hpa -w
```

## Production Considerations

### 1. Model Versioning

- Models stored in PersistentVolume
- Version tracked in `models/current_model_version.txt`
- New models automatically loaded on restart

### 2. Feature Store Updates

- Feature store updated via Dagster pipeline
- Volume mounted to pods
- Consider read-only mounts for production

### 3. Monitoring

- Prometheus metrics at `/metrics`
- Health checks at `/health`
- Integrate with monitoring stack (Prometheus + Grafana)

### 4. Security

- Use secrets for sensitive config
- Enable TLS for ingress
- Network policies for pod isolation
- RBAC for service accounts

### 5. Resource Limits

Adjust in `k8s/deployment-api.yaml`:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"
```

## Dagster Pipeline Deployment

### Local Development

```bash
dagster dev
```

### Production

**Option 1: Dagster Cloud**
- Connect repository to Dagster Cloud
- Configure schedules
- Monitor runs

**Option 2: Self-Hosted**

```bash
# Install Dagster
pip install dagster dagster-webserver

# Run webserver
dagster-webserver -h 0.0.0.0 -p 3000
```

**Option 3: Kubernetes**

Deploy Dagster as Kubernetes job/cronjob for scheduled runs.

## Troubleshooting

### API not starting

```bash
# Check logs
kubectl logs -l app=searchop-api

# Common issues:
# - Model file not found
# - Feature store not found
# - Port conflicts
```

### Model loading errors

```bash
# Verify model exists
kubectl exec -it <pod-name> -- ls -la /app/models/

# Check model version
kubectl exec -it <pod-name> -- cat /app/models/current_model_version.txt
```

### HPA not scaling

```bash
# Check metrics
kubectl top pods -l app=searchop-api

# Verify HPA status
kubectl describe hpa searchop-api-hpa
```

## Next Steps

- [ ] Set up CI/CD for automated deployments
- [ ] Configure monitoring dashboards
- [ ] Implement canary deployments
- [ ] Add shadow mode for model testing
- [ ] Set up alerting


