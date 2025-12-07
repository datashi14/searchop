# Deploy SearchOp to AWS EKS - Step-by-Step Guide

This guide walks through deploying SearchOp to a real AWS EKS cluster. This proves the system is production-ready, not theoretical.

## Prerequisites

### AWS Account Setup

- AWS account with permissions to create:
  - EKS clusters
  - VPC and networking
  - ECR repositories
  - S3 buckets
- **Important**: Use your own dev account, not production accounts

### Required Tools

Install on your local machine:

```bash
# AWS CLI
aws --version  # Should be v2.x

# Terraform
terraform --version  # Should be >= 1.0

# kubectl
kubectl version --client

# Docker
docker --version

# Python 3.11
python --version  # Should be 3.11+
```

### Configure AWS

```bash
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: ap-southeast-2 (or your preferred region)
# - Default output format: json
```

Verify:
```bash
aws sts get-caller-identity
```

## Step 1: Prepare Model + Data Locally

The Dockerfile copies `models/` and `data/processed/` into the image, so generate them first:

```bash
# Clone repo
git clone https://github.com/datashi14/searchop.git
cd searchop

# Setup environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Generate data, features, train model, evaluate
make demo
```

This creates:
- `models/model_v*.pkl` + `models/current_model_version.txt`
- `data/processed/feature_store.parquet`

These will be baked into the Docker image.

## Step 2: Spin Up EKS with Terraform

Navigate to the AWS infrastructure folder:

```bash
cd infra/aws
```

### Configure Region (Optional)

If you want a different region (e.g., Melbourne/ap-southeast-2), either:

**Option A:** Edit `variables.tf`:
```hcl
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-2"
}
```

**Option B:** Pass as variable:
```bash
terraform plan -var 'aws_region=ap-southeast-2'
terraform apply -var 'aws_region=ap-southeast-2'
```

### Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Review plan
terraform plan -var 'aws_region=ap-southeast-2'

# Apply (creates VPC, EKS, S3, ECR)
terraform apply -var 'aws_region=ap-southeast-2'
```

This creates:
- VPC with public/private subnets
- EKS cluster: `searchop-cluster`
- Managed node group (3x t3.medium by default)
- S3 bucket: `searchop-models-dev`
- ECR repository: `searchop-api`

**Important:** Save the outputs, especially `ecr_repository_url`:
```bash
terraform output ecr_repository_url
# Example: "123456789012.dkr.ecr.ap-southeast-2.amazonaws.com/searchop-api"
```

## Step 3: Configure kubectl

Point kubectl at your new cluster:

```bash
aws eks update-kubeconfig \
  --name searchop-cluster \
  --region ap-southeast-2
```

Verify:
```bash
kubectl get nodes
```

You should see your worker nodes in `Ready` state.

## Step 4: Build + Push Docker Image to ECR

### Get ECR URL

```bash
cd infra/aws
ECR_URL=$(terraform output -raw ecr_repository_url)
echo $ECR_URL
cd ../..
```

### Login to ECR

```bash
aws ecr get-login-password --region ap-southeast-2 | \
  docker login --username AWS --password-stdin $ECR_URL
```

### Build Image

```bash
# From project root
docker build -f docker/Dockerfile.api -t searchop-api:latest .
```

### Tag for ECR

```bash
docker tag searchop-api:latest $ECR_URL:latest
```

### Push to ECR

```bash
docker push $ECR_URL:latest
```

## Step 5: Update Kubernetes Deployment

Edit `k8s/deployment-api.yaml`:

### a) Set ECR Image

Find:
```yaml
image: searchop-api:latest
```

Replace with your ECR URL:
```yaml
image: 123456789012.dkr.ecr.ap-southeast-2.amazonaws.com/searchop-api:latest
```

### b) Comment Out Volume Mounts (For Demo)

For a simple demo deployment, comment out the volume sections to use baked-in files:

```yaml
# volumeMounts:
#   - name: models
#     mountPath: /app/models
#   - name: feature-store
#     mountPath: /app/data/processed

# volumes:
#   - name: models
#     persistentVolumeClaim:
#       claimName: searchop-models-pvc
#   - name: feature-store
#     persistentVolumeClaim:
#       claimName: searchop-features-pvc
```

This way the container uses the models and data baked into the Docker image.

**Note:** For production, you'd use S3 + PVCs for dynamic model updates.

## Step 6: Deploy to EKS

From project root:

```bash
kubectl apply -f k8s/deployment-api.yaml
kubectl apply -f k8s/service-api.yaml
```

Check status:

```bash
kubectl get pods
kubectl get svc
```

**Expected:**
- `searchop-api-...` pods in `Running` state
- `READY 1/1`
- `searchop-api` service with `CLUSTER-IP` on port 80

**Troubleshooting:**

If pods are `CrashLoopBackOff`:
```bash
kubectl logs deployment/searchop-api
kubectl describe pod <pod-name>
```

Common issues:
- Image pull errors → Check ECR permissions
- Model not found → Verify image was built after `make demo`
- Port conflicts → Check service configuration

## Step 7: Test the Deployment

### Port Forward

```bash
kubectl port-forward service/searchop-api 8000:80
```

### Test Endpoints

**Health Check:**
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","version":"v1"}
```

**Metrics:**
```bash
curl http://localhost:8000/metrics
# Expected: Prometheus metrics format
```

**API Docs:**
Open in browser: http://localhost:8000/docs

**Ranking Endpoint:**
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

### Load Test

```bash
python scripts/load_test.py --requests 100 --concurrency 10 --url http://localhost:8000
```

**Expected:** P95 latency < 50ms

## Step 8: Verify CI/CD Pipeline

The GitHub Actions workflow should be running automatically.

1. Push any small change to trigger CI:
```bash
git commit --allow-empty -m "Trigger CI"
git push
```

2. Check GitHub Actions: https://github.com/datashi14/searchop/actions

**Expected:** All jobs green:
- ✅ Lint & Type Check
- ✅ Unit Tests
- ✅ Integration Tests
- ✅ Model Evaluation (on main)
- ✅ E2E Tests (on main)

## Step 9: Cleanup (Important!)

To avoid ongoing costs, tear everything down:

### Remove Kubernetes Resources

```bash
kubectl delete -f k8s/service-api.yaml
kubectl delete -f k8s/deployment-api.yaml
```

### Destroy Infrastructure

```bash
cd infra/aws
terraform destroy -var 'aws_region=ap-southeast-2'
```

**Cost Note:** If you only keep the cluster up for a few hours, cost is typically single-digit dollars, not hundreds.

### Optional: Clean ECR Images

From AWS Console:
- ECR → `searchop-api` → Delete images

### Optional: Clean S3 Bucket

From AWS Console:
- S3 → `searchop-models-dev` → Empty bucket → Delete bucket

## Screenshots to Capture

For your portfolio/interviews:

1. **kubectl get pods** - Showing pods in `Running` state
2. **/metrics endpoint** - Browser showing Prometheus metrics
3. **/docs or /health** - Browser showing API is alive
4. **GitHub Actions** - All CI jobs passing
5. **Load test results** - Showing latency < 50ms

## What This Proves

✅ **Real AWS EKS deployment** - Not theoretical  
✅ **API running on real pods** - Actual Kubernetes  
✅ **Metrics and health checks** - Observability works  
✅ **CI/CD pipeline** - Automated testing works  
✅ **Production-ready** - Can deploy in hours  

## Talking Points for Interviews

> "Here's the repo. Here are screenshots of it running on EKS with metrics and CI. If you want, I can spin it up live on a call and hit /rank in front of you."

This demonstrates:
- Real operational experience
- Cloud deployment expertise
- End-to-end system understanding
- Production-ready code

## Next Steps (Optional)

For a more production-like setup:

1. **Use S3 for models** - Update deployment to pull models from S3
2. **Add Ingress** - Configure ALB/ingress controller
3. **Add Monitoring** - CloudWatch Container Insights
4. **Add Logging** - Fluentd/Fluent Bit
5. **Add Secrets** - Use AWS Secrets Manager
6. **Add Autoscaling** - Configure cluster autoscaler

But the current setup already proves production-readiness.

