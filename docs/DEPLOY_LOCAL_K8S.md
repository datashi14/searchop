# Deploy SearchOp to Local Kubernetes (kind)

This guide shows how to deploy SearchOp to a local Kubernetes cluster using [kind](https://kind.sigs.k8s.io/).

## Prerequisites

- Docker installed and running
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) installed
- [kubectl](https://kubernetes.io/docs/tasks/tools/) installed
- Make (optional, but recommended)

## Quick Start

```bash
# 1. Setup local cluster
make kind-setup

# 2. Build and load Docker image
make kind-load-image

# 3. Deploy application
make kind-deploy

# 4. Port forward to access service
kubectl port-forward -n searchop service/searchop-api 8000:80
```

## Manual Steps

### 1. Create Cluster

```bash
kind create cluster --config infra/local-cluster/kind-config.yaml
```

This creates a 3-node cluster (1 control-plane, 2 workers).

### 2. Build Docker Image

```bash
docker build -f docker/Dockerfile.api -t searchop-api:latest .
```

### 3. Load Image to kind

```bash
kind load docker-image searchop-api:latest --name searchop-local
```

### 4. Deploy Application

```bash
kubectl apply -k k8s/overlays/local/
```

### 5. Verify Deployment

```bash
# Check pods
kubectl get pods -n searchop

# Check services
kubectl get services -n searchop

# Check HPA
kubectl get hpa -n searchop
```

### 6. Access Service

```bash
# Port forward
kubectl port-forward -n searchop service/searchop-api 8000:80

# Test health endpoint
curl http://localhost:8000/health

# Test ranking endpoint
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

## Monitoring

### View Logs

```bash
# All pods
kubectl logs -n searchop -l app=searchop-api -f

# Specific pod
kubectl logs -n searchop <pod-name> -f
```

### View Metrics

```bash
# Port forward
kubectl port-forward -n searchop service/searchop-api 8000:80

# Access Prometheus metrics
curl http://localhost:8000/metrics
```

### HPA Scaling

```bash
# Watch HPA
kubectl get hpa -n searchop -w

# Generate load (in another terminal)
while true; do
  curl -X POST "http://localhost:8000/rank" \
    -H "Content-Type: application/json" \
    -d '{"query": "test", "user_id": "u-1", "products": [{"id": 1, "title": "Test", "price": 10, "category": "test"}]}'
  sleep 0.1
done
```

## Cleanup

```bash
# Delete deployment
kubectl delete -k k8s/overlays/local/

# Or tear down entire cluster
make kind-teardown
# or
kind delete cluster --name searchop-local
```

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl describe pod -n searchop <pod-name>

# Common issues:
# - Image not found: Run `make kind-load-image`
# - Resource limits: Check node resources with `kubectl top nodes`
```

### Service not accessible

```bash
# Check service
kubectl describe service -n searchop searchop-api

# Check endpoints
kubectl get endpoints -n searchop searchop-api
```

### HPA not scaling

```bash
# Check HPA status
kubectl describe hpa -n searchop searchop-api-hpa

# Check metrics server
kubectl top pods -n searchop
```

## Next Steps

Once you've verified the local deployment works:

1. **Adapt for Cloud**: The manifests in `k8s/` can be adapted for EKS/GKE/AKS
2. **Add Ingress**: Configure ingress controller for external access
3. **Add Monitoring**: Deploy Prometheus + Grafana stack
4. **Add Logging**: Configure Fluentd/Fluent Bit for log aggregation

## Production Considerations

For production deployment on EKS/GKE/AKS:

1. **Use managed services**: RDS/Cloud SQL for metadata, S3/GCS for models
2. **Configure ingress**: Use ALB/GLB or ingress controller
3. **Set up monitoring**: CloudWatch/Stackdriver/Prometheus
4. **Configure autoscaling**: Adjust HPA based on actual traffic patterns
5. **Security**: Use secrets, network policies, RBAC

See `docs/DEPLOYMENT.md` for more details.


