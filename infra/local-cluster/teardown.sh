#!/bin/bash
# Teardown local Kubernetes cluster

set -e

echo "Deleting local Kubernetes cluster..."

kind delete cluster --name searchop-local || true

echo "Cluster deleted."


