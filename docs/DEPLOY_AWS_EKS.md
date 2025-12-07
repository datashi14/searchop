# Deploy SearchOp to AWS EKS

This guide covers deploying SearchOp to Amazon EKS (Elastic Kubernetes Service).

## Overview

The Terraform configuration in `infra/aws/` provides a complete infrastructure setup for running SearchOp on AWS EKS. This includes:

- EKS cluster with managed node groups
- VPC with public/private subnets
- S3 bucket for model storage
- ECR repository for Docker images
- IAM roles for service access

## Prerequisites

- AWS account with admin permissions
- Terraform >= 1.0 installed
- AWS CLI configured (`aws configure`)
- kubectl installed
- Docker installed (for building images)

## Quick Start

### 1. Configure Terraform

```bash
cd infra/aws

# Review and adjust variables in variables.tf
# Set your preferred AWS region
```

### 2. Initialize and Plan

```bash
terraform init
terraform plan
```

### 3. Deploy Infrastructure

```bash
terraform apply
```

This creates:
- VPC and networking
- EKS cluster
- Node groups
- S3 bucket
- ECR repository

### 4. Configure kubectl

```bash
aws eks update-kubeconfig \
  --name searchop-cluster \
  --region us-west-2
```

### 5. Build and Push Docker Image

```bash
# Get ECR login
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-west-2.amazonaws.com

# Build image
docker build -f docker/Dockerfile.api -t searchop-api:latest .

# Tag for ECR
docker tag searchop-api:latest \
  <account-id>.dkr.ecr.us-west-2.amazonaws.com/searchop-api:latest

# Push
docker push <account-id>.dkr.ecr.us-west-2.amazonaws.com/searchop-api:latest
```

### 6. Update Kubernetes Manifests

Edit `k8s/deployment-api.yaml` to use ECR image:

```yaml
image: <account-id>.dkr.ecr.us-west-2.amazonaws.com/searchop-api:latest
```

### 7. Deploy Application

```bash
kubectl apply -f k8s/
```

### 8. Configure S3 Access

Update deployment to use S3 for models:

```yaml
env:
- name: MODEL_S3_BUCKET
  value: "searchop-models-dev"
- name: AWS_REGION
  value: "us-west-2"
```

## Production Considerations

### 1. Use Managed Services

- **RDS**: For metadata storage
- **ElastiCache**: For caching
- **Secrets Manager**: For sensitive config

### 2. Configure Ingress

```bash
# Install ALB Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/aws/deploy.yaml
```

### 3. Set Up Monitoring

- CloudWatch Container Insights
- Prometheus + Grafana
- X-Ray for distributed tracing

### 4. Configure Autoscaling

- Cluster Autoscaler
- Karpenter (for better cost optimization)
- HPA (already configured)

### 5. Security

- Network policies
- Pod security policies
- RBAC
- Secrets management

## Cost Estimation

For a small production setup:

- EKS cluster: ~$72/month
- 3x t3.medium nodes: ~$90/month
- S3 storage: ~$1/month
- Data transfer: Variable

**Total**: ~$150-200/month

## Troubleshooting

### Cluster not accessible

```bash
# Check cluster status
aws eks describe-cluster --name searchop-cluster --region us-west-2

# Verify kubectl config
kubectl cluster-info
```

### Pods not starting

```bash
# Check events
kubectl get events --sort-by='.lastTimestamp'

# Check pod logs
kubectl logs <pod-name> -n default
```

### S3 access issues

```bash
# Verify IAM role
kubectl describe pod <pod-name> | grep AWS_ROLE

# Test S3 access from pod
kubectl exec -it <pod-name> -- aws s3 ls s3://searchop-models-dev/
```

## Cleanup

```bash
# Delete application
kubectl delete -f k8s/

# Delete infrastructure
cd infra/aws
terraform destroy
```

## Notes

This Terraform configuration was created as a reference implementation. It demonstrates the infrastructure patterns needed for a production deployment but has not been kept running in a persistent AWS account to avoid ongoing costs.

The code and manifests are production-ready and can be deployed to AWS with appropriate credentials and permissions.


