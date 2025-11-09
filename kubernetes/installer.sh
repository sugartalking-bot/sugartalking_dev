#!/bin/bash
#
# Sugartalking Kubernetes Installer
# Linux/macOS installation script
#
# Usage: ./installer.sh [options]
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${NAMESPACE:-default}"
IMAGE_REGISTRY="${IMAGE_REGISTRY:-ghcr.io/builderoftheworlds}"
IMAGE_NAME="sugartalking"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found. Please install kubectl first."
        exit 1
    fi

    # Check if kubectl can connect to cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi

    log_success "Prerequisites check passed"
}

create_namespace() {
    log_info "Checking namespace '$NAMESPACE'..."

    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_info "Namespace '$NAMESPACE' already exists"
    else
        if [ "$NAMESPACE" != "default" ]; then
            log_info "Creating namespace '$NAMESPACE'..."
            kubectl create namespace "$NAMESPACE"
            log_success "Namespace created"
        fi
    fi
}

setup_github_secret() {
    log_info "Setting up GitHub token for error reporting..."

    if kubectl get secret sugartalking-secrets -n "$NAMESPACE" &> /dev/null; then
        log_info "GitHub secret already exists"
        return
    fi

    read -p "Do you want to configure GitHub error reporting? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter GitHub personal access token: " -s github_token
        echo

        if [ -n "$github_token" ]; then
            kubectl create secret generic sugartalking-secrets \
                --from-literal=GITHUB_TOKEN="$github_token" \
                -n "$NAMESPACE"
            log_success "GitHub secret created"
        else
            log_warning "No token provided, skipping secret creation"
        fi
    else
        log_info "Skipping GitHub secret setup"
    fi
}

apply_manifests() {
    log_info "Applying Kubernetes manifests..."

    # Update namespace in manifests if not default
    if [ "$NAMESPACE" != "default" ]; then
        log_info "Updating namespace in manifests to '$NAMESPACE'..."
        find base/ -name "*.yaml" -type f -exec sed -i.bak "s/namespace: default/namespace: $NAMESPACE/g" {} \;
    fi

    # Apply in order
    kubectl apply -f base/persistentvolumeclaim.yaml
    kubectl apply -f base/configmap.yaml
    kubectl apply -f base/deployment.yaml
    kubectl apply -f base/service.yaml

    # Ask about ingress
    read -p "Do you want to install Ingress? (requires ingress controller) (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kubectl apply -f base/ingress.yaml
        log_success "Ingress created"
    fi

    # Cleanup backup files
    find base/ -name "*.yaml.bak" -type f -delete

    log_success "Manifests applied"
}

wait_for_deployment() {
    log_info "Waiting for deployment to be ready..."

    kubectl wait --for=condition=available --timeout=300s \
        deployment/sugartalking -n "$NAMESPACE"

    log_success "Deployment is ready!"
}

display_access_info() {
    log_info "Fetching access information..."
    echo
    echo "=========================================="
    echo "  Sugartalking Installation Complete! 🎉"
    echo "=========================================="
    echo

    # Get pod name
    POD_NAME=$(kubectl get pods -n "$NAMESPACE" -l app=sugartalking -o jsonpath='{.items[0].metadata.name}')
    echo "Pod Name: $POD_NAME"
    echo

    # Check for ingress
    if kubectl get ingress sugartalking -n "$NAMESPACE" &> /dev/null; then
        HOSTNAME=$(kubectl get ingress sugartalking -n "$NAMESPACE" -o jsonpath='{.spec.rules[0].host}')
        echo "Access URL: http://$HOSTNAME"
        echo
        log_info "Make sure '$HOSTNAME' is in your /etc/hosts file pointing to your cluster IP"
    else
        echo "To access Sugartalking, use port-forward:"
        echo "  kubectl port-forward -n $NAMESPACE svc/sugartalking 5000:80"
        echo
        echo "Then visit: http://localhost:5000"
    fi

    echo
    echo "Admin Panel: http://localhost:5000/admin"
    echo
    echo "View logs:"
    echo "  kubectl logs -n $NAMESPACE -l app=sugartalking -f"
    echo
    echo "=========================================="
}

cleanup_on_error() {
    log_error "Installation failed. Rolling back..."
    kubectl delete -f base/ -n "$NAMESPACE" --ignore-not-found=true
    exit 1
}

# Main installation
main() {
    echo
    echo "╔═══════════════════════════════════════╗"
    echo "║   Sugartalking Kubernetes Installer   ║"
    echo "║        Universal AVR Control          ║"
    echo "╚═══════════════════════════════════════╝"
    echo

    # Change to script directory
    cd "$(dirname "$0")"

    # Trap errors
    trap cleanup_on_error ERR

    # Run installation steps
    check_prerequisites
    create_namespace
    setup_github_secret
    apply_manifests
    wait_for_deployment
    display_access_info

    log_success "Installation completed successfully!"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --namespace|-n)
            NAMESPACE="$2"
            shift 2
            ;;
        --image)
            IMAGE_REGISTRY="$2"
            shift 2
            ;;
        --tag|-t)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo
            echo "Options:"
            echo "  -n, --namespace NAME    Kubernetes namespace (default: default)"
            echo "  --image REGISTRY        Container registry (default: ghcr.io/builderoftheworlds)"
            echo "  -t, --tag TAG           Image tag (default: latest)"
            echo "  -h, --help              Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main installation
main
