#!/bin/bash
set -e

# Get the directory of this script and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="sugartalking"
IMAGE_TAG="latest"
REGISTRY="localhost:5001"
DOCKERFILE="docker/Dockerfile"
KUBERNETES_DIR="kubernetes"

echo -e "${GREEN}Starting build and deploy process...${NC}"
echo -e "${YELLOW}Working directory: ${PROJECT_ROOT}${NC}\n"

# Step 1: Build Docker image
echo -e "${YELLOW}[1/5] Building Docker image...${NC}"
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -f ${DOCKERFILE} .
echo -e "${GREEN}✓ Image built successfully${NC}\n"

# Step 2: Tag for local registry
echo -e "${YELLOW}[2/5] Tagging image for local registry...${NC}"
docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
echo -e "${GREEN}✓ Image tagged${NC}\n"

# Step 3: Push to local registry
echo -e "${YELLOW}[3/5] Pushing to local registry...${NC}"
docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
echo -e "${GREEN}✓ Image pushed to registry${NC}\n"

# Step 4: Apply Kubernetes manifests
echo -e "${YELLOW}[4/5] Applying Kubernetes manifests...${NC}"
kubectl apply -f ${KUBERNETES_DIR}/base/
echo -e "${GREEN}✓ Manifests applied${NC}\n"

# Step 5: Restart deployment to pull new image
echo -e "${YELLOW}[5/5] Restarting deployment...${NC}"
kubectl rollout restart deployment/${IMAGE_NAME} -n default
echo -e "${GREEN}✓ Deployment restarted${NC}\n"

# Wait for rollout to complete
echo -e "${YELLOW}Waiting for rollout to complete...${NC}"
kubectl rollout status deployment/${IMAGE_NAME} -n default --timeout=300s

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
POD_NAME=$(kubectl get pods -n default -l app=${IMAGE_NAME} -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n default ${POD_NAME} -- python scripts/migrate_all_commands.py
echo -e "${GREEN}✓ Migrations completed${NC}\n"

echo -e "\n${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  Deployment completed successfully!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}\n"

# Show pod status
echo -e "${YELLOW}Current pod status:${NC}"
kubectl get pods -n default -l app=${IMAGE_NAME}

echo -e "\n${YELLOW}To view logs, run:${NC}"
echo -e "  kubectl logs -f -n default -l app=${IMAGE_NAME}"
