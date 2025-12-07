# Local Kubernetes Deployment

This overlay configures the SearchOp deployment for local kind clusters.

## Differences from Production

- Uses local Docker image (`searchop-api:latest`)
- Removes PersistentVolumeClaims (uses local filesystem)
- Simplified for local testing

## Usage

```bash
# Setup cluster
./infra/local-cluster/setup.sh

# Build and load image
make kind-load-image

# Deploy
kubectl apply -k k8s/overlays/local/

# Port forward
kubectl port-forward -n searchop service/searchop-api 8000:80

# Test
curl http://localhost:8000/health
```

