#!/bin/bash
# Helper script for deploying SearchOp to AWS EKS
# Usage: ./scripts/deploy_to_eks.sh [region]

set -e

REGION=${1:-ap-southeast-2}
CLUSTER_NAME="searchop-cluster"

echo "=========================================="
echo "SearchOp EKS Deployment Helper"
echo "=========================================="
echo "Region: $REGION"
echo "Cluster: $CLUSTER_NAME"
echo ""

# Check prerequisites
echo "Checking prerequisites..."
command -v aws >/dev/null 2>&1 || { echo "Error: aws CLI not found"; exit 1; }
command -v terraform >/dev/null 2>&1 || { echo "Error: terraform not found"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "Error: kubectl not found"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Error: docker not found"; exit 1; }
echo "✅ All prerequisites met"
echo ""

# Step 1: Check if model/data exist
echo "Step 1: Checking for model and data..."
if [ ! -f "models/model_v1.pkl" ] || [ ! -f "data/processed/feature_store.parquet" ]; then
    echo "⚠️  Model or data not found. Running 'make demo'..."
    make demo
else
    echo "✅ Model and data found"
fi
echo ""

# Step 2: Deploy infrastructure
echo "Step 2: Deploying infrastructure with Terraform..."
cd infra/aws
if [ ! -d ".terraform" ]; then
    terraform init
fi

echo "Running terraform plan..."
terraform plan -var "aws_region=$REGION"

read -p "Apply terraform changes? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    terraform apply -var "aws_region=$REGION"
    
    # Get outputs
    ECR_URL=$(terraform output -raw ecr_repository_url)
    echo ""
    echo "✅ Infrastructure deployed"
    echo "ECR URL: $ECR_URL"
else
    echo "Skipping terraform apply"
    ECR_URL=$(terraform output -raw ecr_repository_url 2>/dev/null || echo "")
    if [ -z "$ECR_URL" ]; then
        echo "Error: ECR URL not found. Run 'terraform apply' first."
        exit 1
    fi
fi
cd ../..
echo ""

# Step 3: Configure kubectl
echo "Step 3: Configuring kubectl..."
aws eks update-kubeconfig --name $CLUSTER_NAME --region $REGION
echo "✅ kubectl configured"
kubectl get nodes
echo ""

# Step 4: Build and push Docker image
echo "Step 4: Building and pushing Docker image..."
echo "ECR URL: $ECR_URL"

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region $REGION | \
    docker login --username AWS --password-stdin $ECR_URL

# Build
echo "Building Docker image..."
docker build -f docker/Dockerfile.api -t searchop-api:latest .

# Tag
echo "Tagging image..."
docker tag searchop-api:latest $ECR_URL:latest

# Push
echo "Pushing to ECR..."
docker push $ECR_URL:latest
echo "✅ Image pushed to ECR"
echo ""

# Step 5: Update deployment manifest
echo "Step 5: Updating deployment manifest..."
# Create a temporary deployment file with ECR URL
sed "s|image: searchop-api:latest|image: $ECR_URL:latest|g" \
    k8s/deployment-api.yaml > k8s/deployment-api-eks.yaml

echo "✅ Deployment manifest updated: k8s/deployment-api-eks.yaml"
echo ""

# Step 6: Deploy to Kubernetes
echo "Step 6: Deploying to Kubernetes..."
kubectl apply -f k8s/deployment-api-eks.yaml
kubectl apply -f k8s/service-api.yaml

echo "Waiting for deployment..."
kubectl wait --for=condition=available deployment/searchop-api -n default --timeout=300s || true

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Check status:"
echo "  kubectl get pods"
echo "  kubectl get svc"
echo ""
echo "Port forward:"
echo "  kubectl port-forward service/searchop-api 8000:80"
echo ""
echo "Test:"
echo "  curl http://localhost:8000/health"
echo "  curl http://localhost:8000/metrics"
echo ""

