#!/usr/bin/env bash

# Script to update Azure secret in Kubernetes using .ark.env file
# Usage: ./scripts/update-azure-secret.sh

set -e -o pipefail

# Colors for output
green='\033[0;32m'
red='\033[0;31m'
yellow='\033[1;33m'
blue='\033[0;34m'
nc='\033[0m'

echo -e "${blue}Updating Azure secret in Kubernetes using .ark.env${nc}"
echo ""

# Check if .ark.env exists
if [ ! -f ".ark.env" ]; then
    echo -e "${red}Error: .ark.env file not found${nc}"
    echo "Please create a .ark.env file with your Azure configuration:"
    echo "  ARK_QUICKSTART_MODEL_TYPE=azure"
    echo "  ARK_QUICKSTART_MODEL_VERSION=gpt-35-turbo"
    echo "  ARK_QUICKSTART_BASE_URL=https://your-azure-endpoint"
    echo "  ARK_QUICKSTART_API_VERSION=2024-04-01-preview"
    echo "  ARK_QUICKSTART_API_KEY=your-api-key"
    exit 1
fi

# Source the .ark.env file
source .ark.env

# Validate required variables
if [ -z "$ARK_QUICKSTART_API_KEY" ]; then
    echo -e "${red}Error: ARK_QUICKSTART_API_KEY not set in .ark.env${nc}"
    exit 1
fi

if [ -z "$ARK_QUICKSTART_BASE_URL" ]; then
    echo -e "${red}Error: ARK_QUICKSTART_BASE_URL not set in .ark.env${nc}"
    exit 1
fi

# Display current configuration (hide API key)
echo -e "${blue}Current Azure configuration:${nc}"
echo "  Model Type: ${ARK_QUICKSTART_MODEL_TYPE:-azure}"
echo "  Model Version: ${ARK_QUICKSTART_MODEL_VERSION:-gpt-35-turbo}"
echo "  Base URL: ${ARK_QUICKSTART_BASE_URL}"
echo "  API Version: ${ARK_QUICKSTART_API_VERSION:-2024-04-01-preview}"
echo "  API Key: ${ARK_QUICKSTART_API_KEY:0:20}..."
echo ""

# Update the Azure secret
echo -e "${blue}Updating Azure secret...${nc}"
kubectl create secret generic azure-openai-secret \
    --from-literal=token="$ARK_QUICKSTART_API_KEY" \
    --dry-run=client -o yaml | kubectl apply -f -

if [ $? -eq 0 ]; then
    echo -e "${green}✔${nc} Azure secret updated successfully"
else
    echo -e "${red}✗${nc} Failed to update Azure secret"
    exit 1
fi

# Update the default model configuration
echo -e "${blue}Updating default model configuration...${nc}"
API_KEY=$(echo -n "$ARK_QUICKSTART_API_KEY" | base64 | tr -d '\n' | tr -d ' ')
BASE_URL="$ARK_QUICKSTART_BASE_URL"
MODEL_TYPE="${ARK_QUICKSTART_MODEL_TYPE:-azure}"
MODEL_VERSION="${ARK_QUICKSTART_MODEL_VERSION:-gpt-35-turbo}"
API_VERSION="${ARK_QUICKSTART_API_VERSION:-2024-04-01-preview}"

export API_KEY BASE_URL MODEL_TYPE MODEL_VERSION API_VERSION
envsubst < samples/quickstart/default-model.yaml | kubectl apply -f -

if [ $? -eq 0 ]; then
    echo -e "${green}✔${nc} Default model configuration updated successfully"
else
    echo -e "${red}✗${nc} Failed to update default model configuration"
    exit 1
fi

echo ""
echo -e "${green}Azure secret and model configuration updated successfully!${nc}"
echo ""
echo -e "${blue}You can test the configuration with:${nc}"
echo "  ./scripts/query.sh agent/sample-agent \"Hello, test the Azure connection\""
echo ""
echo -e "${blue}Or check the model status with:${nc}"
echo "  kubectl get model default"