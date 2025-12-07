# Quick EKS Deployment Checklist

Use this checklist when deploying SearchOp to AWS EKS.

## ✅ Prerequisites Check

- [x] AWS CLI installed (`aws --version`)
- [x] Terraform installed (`terraform --version`) ✅ v1.14.1
- [x] kubectl installed (`kubectl version --client`)
- [x] Docker installed (`docker --version`)
- [x] Python 3.11+ installed (`python --version`)
- [ ] AWS configured (`aws configure`)
- [ ] AWS credentials verified (`aws sts get-caller-identity`)

## 📋 Deployment Steps

### 1. Prepare Model & Data
```bash
# From project root
make demo
```
**Check:** `models/model_v1.pkl` and `data/processed/feature_store.parquet` exist

### 2. Configure AWS
```bash
aws configure
# Enter: Access Key, Secret Key, Region (ap-southeast-2), Output (json)

aws sts get-caller-identity
# Verify: Should show your AWS account ID
```

### 3. Deploy Infrastructure
```bash
cd infra/aws

# Initialize Terraform
terraform init

# Review plan
terraform plan -var 'aws_region=ap-southeast-2'

# Apply (creates EKS, VPC, S3, ECR)
terraform apply -var 'aws_region=ap-southeast-2'
# Type: yes

# Get ECR URL
terraform output ecr_repository_url
# Save this URL!
```

### 4. Configure kubectl
```bash
aws eks update-kubeconfig \
  --name searchop-cluster \
  --region ap-southeast-2

kubectl get nodes
# Should show 3 nodes in Ready state
```

### 5. Build & Push Docker Image
```bash
# Go back to project root
cd ../../

# Get ECR URL (from step 3)
ECR_URL="<your-ecr-url>"  # e.g., 123456789012.dkr.ecr.ap-southeast-2.amazonaws.com/searchop-api

# Login to ECR
aws ecr get-login-password --region ap-southeast-2 | \
  docker login --username AWS --password-stdin $ECR_URL

# Build image
docker build -f docker/Dockerfile.api -t searchop-api:latest .

# Tag for ECR
docker tag searchop-api:latest $ECR_URL:latest

# Push
docker push $ECR_URL:latest
```

### 6. Update Deployment Manifest
Edit `k8s/deployment-api.yaml`:

**Change:**
```yaml
image: searchop-api:latest
```

**To:**
```yaml
image: <your-ecr-url>:latest  # Use ECR_URL from step 5
```

**Comment out volumes** (for demo):
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

### 7. Deploy to Kubernetes
```bash
kubectl apply -f k8s/deployment-api.yaml
kubectl apply -f k8s/service-api.yaml

# Check status
kubectl get pods
kubectl get svc
```

**Expected:**
- Pods: `Running` with `READY 1/1`
- Service: `ClusterIP` on port 80

### 8. Test Deployment
```bash
# Port forward
kubectl port-forward service/searchop-api 8000:80

# In another terminal, test:
curl http://localhost:8000/health
curl http://localhost:8000/metrics
curl -X POST "http://localhost:8000/rank" \
  -H "Content-Type: application/json" \
  -d '{"query": "shoes", "user_id": "u-1", "products": [{"id": 1, "title": "Test", "price": 10, "category": "test"}]}'
```

### 9. Capture Screenshots
- [ ] `kubectl get pods` showing Running pods
- [ ] Browser: `/metrics` endpoint
- [ ] Browser: `/health` or `/docs` endpoint
- [ ] Load test results (if run)

### 10. Cleanup (Important!)
```bash
# Delete Kubernetes resources
kubectl delete -f k8s/service-api.yaml
kubectl delete -f k8s/deployment-api.yaml

# Destroy infrastructure
cd infra/aws
terraform destroy -var 'aws_region=ap-southeast-2'
# Type: yes
```

## 🎯 Success Criteria

✅ Pods running and healthy  
✅ `/health` returns 200  
✅ `/metrics` shows Prometheus format  
✅ `/rank` returns ranked products  
✅ All endpoints accessible via port-forward  

## 💰 Cost Estimate

**For ~2 hours of testing:**
- EKS cluster: ~$0.20
- EC2 instances (3x t3.medium): ~$0.30
- Data transfer: ~$0.10
- **Total: < $1 USD**

## 🐛 Troubleshooting

**Pods not starting:**
```bash
kubectl logs deployment/searchop-api
kubectl describe pod <pod-name>
```

**Image pull errors:**
- Check ECR permissions
- Verify image was pushed: `aws ecr describe-images --repository-name searchop-api`

**Service not accessible:**
```bash
kubectl get endpoints searchop-api
kubectl describe service searchop-api
```

## 📝 Notes

- Keep ECR URL handy (you'll need it for deployment manifest)
- Terraform outputs are saved - you can retrieve them later with `terraform output`
- Screenshots prove real deployment - take them!
- Clean up promptly to avoid costs

