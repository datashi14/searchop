#!/bin/bash
# Setup local Kubernetes cluster with kind

set -e

echo "Setting up local Kubernetes cluster for SearchOp..."

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo "Error: kind not found. Install from https://kind.sigs.k8s.io/"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl not found. Install from https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# Create cluster
echo "Creating kind cluster..."
kind create cluster --config infra/local-cluster/kind-config.yaml

# Wait for cluster to be ready
echo "Waiting for cluster to be ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=300s

# Create namespace
kubectl create namespace searchop || true

echo ""
echo "=========================================="
echo "Local cluster ready!"
echo "=========================================="
echo ""
echo "Cluster name: searchop-local"
echo "To delete: kind delete cluster --name searchop-local"
echo ""
echo "Next steps:"
echo "  1. Build and load Docker image: make kind-load-image"
echo "  2. Deploy: make kind-deploy"
echo ""

