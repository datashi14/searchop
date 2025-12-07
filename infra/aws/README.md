# AWS EKS Deployment

This Terraform configuration provides a skeleton for deploying SearchOp to AWS EKS.

## Status

**This is a reference implementation.** The Terraform code demonstrates the infrastructure pattern but has not been deployed to a persistent AWS account to avoid ongoing costs.

## What This Includes

- **EKS Cluster**: Managed Kubernetes cluster
- **VPC**: Isolated network with public/private subnets
- **Node Groups**: Auto-scaling worker nodes
- **S3 Bucket**: Model storage with versioning
- **ECR Repository**: Docker image registry
- **IAM Roles**: Permissions for S3 access

## Prerequisites

- AWS account with appropriate permissions
- Terraform >= 1.0
- AWS CLI configured
- kubectl installed

## Usage

```bash
cd infra/aws

# Initialize Terraform
terraform init

# Review plan
terraform plan

# Apply (creates infrastructure)
terraform apply

# Configure kubectl
aws eks update-kubeconfig --name searchop-cluster --region us-west-2

# Deploy application
kubectl apply -k ../../k8s/
```

## Cost Considerations

- EKS cluster: ~$0.10/hour (~$72/month)
- EC2 instances: Depends on instance types
- S3 storage: Minimal for models
- Data transfer: Variable

**Estimated monthly cost**: $100-200 for a small cluster

## Adapting for Production

1. **Use managed services**: RDS for metadata, ElastiCache for caching
2. **Add monitoring**: CloudWatch, X-Ray
3. **Configure autoscaling**: Cluster autoscaler, Karpenter
4. **Security**: Network policies, pod security policies
5. **Backup**: Automated S3 backups, RDS snapshots

## Cleanup

```bash
# Destroy infrastructure
terraform destroy
```

**Warning**: This will delete all resources. Ensure you have backups.

## Notes

- This configuration was tested once during development
- The cluster is not kept running to avoid costs
- All manifests in `k8s/` are compatible with EKS
- See `docs/DEPLOYMENT.md` for deployment steps

## Next Steps

For a production deployment:

1. Review and customize variables
2. Set up remote state (S3 backend)
3. Configure CI/CD for automated deployments
4. Set up monitoring and alerting
5. Implement backup strategies


