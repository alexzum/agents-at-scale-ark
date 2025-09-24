#!/bin/bash
# Demo Secrets Setup Script
# Creates/updates secrets for banking demo from .ark.env

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

echo "🔐 Banking Demo Secrets Setup"
echo "=============================="

# Check if .ark.env exists
if [ ! -f ".ark.env" ]; then
    log_error ".ark.env file not found in current directory"
    echo "Please run this script from the project root where .ark.env is located"
    exit 1
fi

# Load environment variables from .ark.env
log_info "Loading environment variables from .ark.env..."
source .ark.env

# Validate required variables
required_vars=(
    "ARK_QUICKSTART_API_KEY"
    "ARK_QUICKSTART_BASE_URL"
    "ARK_QUICKSTART_API_VERSION"
    "ARK_QUICKSTART_MODEL_VERSION"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        log_error "Required environment variable $var is not set in .ark.env"
        exit 1
    fi
done

log_success "All required environment variables found"

# Check if demo-bank namespace exists
if ! kubectl get namespace demo-bank &> /dev/null; then
    log_info "Creating demo-bank namespace..."
    kubectl create namespace demo-bank
    log_success "Created demo-bank namespace"
else
    log_info "demo-bank namespace already exists"
fi

# Create or update the secret
log_info "Creating/updating demo-bank-secrets..."

kubectl create secret generic demo-bank-secrets \
    --namespace=demo-bank \
    --from-literal=api-key="$ARK_QUICKSTART_API_KEY" \
    --from-literal=base-url="$ARK_QUICKSTART_BASE_URL" \
    --from-literal=api-version="$ARK_QUICKSTART_API_VERSION" \
    --from-literal=model-version="$ARK_QUICKSTART_MODEL_VERSION" \
    --dry-run=client -o yaml | kubectl apply -f -

log_success "demo-bank-secrets created/updated successfully"

# Restart any existing models to pick up new secret values
if kubectl get model default -n demo-bank &> /dev/null; then
    log_info "Restarting model to pick up new secret values..."
    kubectl patch model default -n demo-bank --type=merge -p '{"metadata":{"annotations":{"kubectl.kubernetes.io/restartedAt":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}}}'
    log_success "Model restart triggered"
fi

# Show secret contents (masked)
echo
log_info "Secret contents (values masked for security):"
echo "📋 Secret: demo-bank-secrets"
echo "   - api-key: ${ARK_QUICKSTART_API_KEY:0:20}..."
echo "   - base-url: $ARK_QUICKSTART_BASE_URL"
echo "   - api-version: $ARK_QUICKSTART_API_VERSION"
echo "   - model-version: $ARK_QUICKSTART_MODEL_VERSION"

echo
log_success "Demo secrets setup completed!"
echo
log_info "Next steps:"
echo "1. Deploy demo resources: kubectl apply -f demo-resources/banking-demo-all.yaml"
echo "2. Wait for agents to be ready: kubectl get agents -n demo-bank -w"
echo "3. Test the demo: See DEMO_GUIDE.md for complete instructions"

echo
log_info "To refresh secrets when .ark.env changes:"
echo "   ./demo-resources/setup-demo-secrets.sh"
