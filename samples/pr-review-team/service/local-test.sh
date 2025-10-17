#!/bin/bash
set -e

echo "=== ARK PR Reviewer Local Test Script ==="
echo ""

# Load .env file if it exists
if [ -f .env ]; then
    echo "Loading configuration from .env file..."
    set -a
    source .env
    set +a
    echo "✅ Configuration loaded"
else
    echo "⚠️  No .env file found. Creating from example..."
    if [ -f .env.local.example ]; then
        cp .env.local.example .env
        echo "✅ Created .env file. Please edit it with your GitHub token and settings."
        echo ""
        echo "Required: Set GITHUB_TOKEN in .env file"
        exit 1
    else
        echo "❌ .env.local.example not found"
        exit 1
    fi
fi

if [ -z "$GITHUB_TOKEN" ] || [ "$GITHUB_TOKEN" = "ghp_your_token_here" ]; then
    echo "❌ GITHUB_TOKEN not set in .env file"
    echo "Please edit .env and set your GitHub token"
    echo "Get a token from: https://github.com/settings/tokens"
    exit 1
fi

NAMESPACE="default"
REPO="${1:-mckinsey/agents-at-scale-ark}"
PR_NUMBER="${2}"

if [ -z "$PR_NUMBER" ]; then
    echo "Usage: ./local-test.sh [repository] <pr_number>"
    echo "Example: ./local-test.sh mckinsey/agents-at-scale-ark 123"
    echo ""
    echo "Fetching last 5 closed PRs from $REPO..."
    gh pr list --repo "$REPO" --state closed --limit 5 --json number,title,headRefName
    echo ""
    read -p "Enter PR number to test: " PR_NUMBER
fi

if [ -z "$PR_NUMBER" ]; then
    echo "❌ No PR number provided"
    exit 1
fi

echo ""
echo "=== Configuration ==="
echo "Repository: $REPO"
echo "PR Number: $PR_NUMBER"
echo "Namespace: $NAMESPACE"
echo ""

echo "=== Step 1: Check Prerequisites ==="

if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Kubernetes cluster not accessible"
    echo "Please start Docker Desktop or minikube"
    exit 1
fi
echo "✅ Kubernetes cluster accessible"

if ! kubectl get namespace ark-system &> /dev/null; then
    echo "⚠️  ARK not installed. Installing..."
    ark install || {
        echo "❌ Failed to install ARK"
        exit 1
    }
fi
echo "✅ ARK installed"

echo ""
echo "=== Step 2: Setup Namespace and Secrets ==="

kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
echo "✅ Namespace created/verified"

kubectl create secret generic ark-pr-reviewer-secrets \
    --from-literal=github-token="$GITHUB_TOKEN" \
    --from-literal=jira-base-url="http://localhost" \
    --from-literal=jira-username="test" \
    --from-literal=jira-api-token="test" \
    --from-literal=azure-openai-base-url="${AZURE_OPENAI_BASE_URL:-http://localhost}" \
    --from-literal=azure-openai-api-key="${AZURE_OPENAI_API_KEY:-test}" \
    --namespace=$NAMESPACE \
    --dry-run=client -o yaml | kubectl apply -f -
echo "✅ Secrets created/updated"

echo ""
echo "=== Step 3: Deploy ARK Resources ==="

kubectl apply -f ../agents/code-quality-reviewer.yaml -n $NAMESPACE
kubectl apply -f ../agents/functionality-analyzer.yaml -n $NAMESPACE
kubectl apply -f ../teams/pr-review-team.yaml -n $NAMESPACE

echo "✅ ARK resources deployed"

sleep 2

echo "Using default model from default namespace:"
kubectl get model default -n default
echo ""
kubectl get agents,teams -n $NAMESPACE

echo ""
echo "=== Step 4: Get PR Information ==="

PR_INFO=$(gh pr view $PR_NUMBER --repo "$REPO" --json headRefName,headRefOid)
BRANCH_NAME=$(echo "$PR_INFO" | jq -r '.headRefName')
COMMIT_SHA=$(echo "$PR_INFO" | jq -r '.headRefOid')

echo "Branch: $BRANCH_NAME"
echo "Commit: $COMMIT_SHA"

echo ""
echo "=== Step 5: Create Review Request ==="

REVIEW_REQUEST=$(cat <<EOF
{
  "repository": "$REPO",
  "pr_number": $PR_NUMBER,
  "branch_name": "$BRANCH_NAME",
  "commit_sha": "$COMMIT_SHA"
}
EOF
)

echo "Request payload:"
echo "$REVIEW_REQUEST" | jq .

echo ""
echo "=== Step 6: Check if service is running ==="

# Use API_PORT from .env, default to 8080
SERVICE_PORT="${API_PORT:-8080}"
SERVICE_URL="http://localhost:${SERVICE_PORT}"

if curl -s "${SERVICE_URL}/health" &> /dev/null; then
    echo "✅ Service already running at ${SERVICE_URL}"
    SERVICE_RUNNING=true
else
    echo "⚠️  Service not running at ${SERVICE_URL}"
    echo ""
    echo "Starting service in background..."
    echo ""
    
    # Check if dependencies are installed
    if [ ! -d ".venv" ]; then
        echo "Installing dependencies..."
        make init
    fi
    
    # Start service in background
    echo "Starting FastAPI service on port ${SERVICE_PORT}..."
    nohup uv run uvicorn ark_pr_reviewer.api:app --host 0.0.0.0 --port ${SERVICE_PORT} > /tmp/ark-pr-reviewer.log 2>&1 &
    SERVICE_PID=$!
    
    echo "Service PID: $SERVICE_PID"
    echo "Logs: /tmp/ark-pr-reviewer.log"
    echo ""
    
    # Wait for service to start
    echo "Waiting for service to start..."
    for i in {1..30}; do
        if curl -s "${SERVICE_URL}/health" &> /dev/null; then
            echo "✅ Service started successfully!"
            SERVICE_RUNNING=true
            break
        fi
        echo -n "."
        sleep 1
    done
    echo ""
    
    if [ "$SERVICE_RUNNING" != "true" ]; then
        echo "❌ Service failed to start. Check logs:"
        echo "    tail -f /tmp/ark-pr-reviewer.log"
        exit 1
    fi
fi

echo ""
echo "=== Step 7: Trigger Review ==="

RESPONSE=$(curl -s -X POST "${SERVICE_URL}/review/pr" \
    -H "Content-Type: application/json" \
    -d "$REVIEW_REQUEST")

echo "Response:"
echo "$RESPONSE" | jq .

REVIEW_ID=$(echo "$RESPONSE" | jq -r '.review_id // empty')

if [ -z "$REVIEW_ID" ]; then
    echo "❌ Failed to get review ID"
    exit 1
fi

echo ""
echo "✅ Review initiated: $REVIEW_ID"
echo ""

echo "=== Step 8: Monitor Progress ==="

echo "Waiting for query to be created..."
sleep 5

QUERY_NAME=$(kubectl get queries -n $NAMESPACE --sort-by=.metadata.creationTimestamp -o json | \
    jq -r ".items[] | select(.metadata.labels.\"review-id\" == \"$REVIEW_ID\") | .metadata.name" | \
    head -1)

if [ -z "$QUERY_NAME" ]; then
    echo "⚠️  Query not found yet. Listing all queries:"
    kubectl get queries -n $NAMESPACE
    echo ""
    echo "Check service logs for errors"
    exit 1
fi

echo "✅ Query created: $QUERY_NAME"
echo ""

echo "Waiting for query completion (timeout: 5 minutes)..."

TIMEOUT=300
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    PHASE=$(kubectl get query $QUERY_NAME -n $NAMESPACE -o jsonpath='{.status.phase}' 2>/dev/null || echo "")
    
    if [ "$PHASE" = "done" ]; then
        echo "✅ Query completed successfully!"
        break
    elif [ "$PHASE" = "error" ]; then
        echo "❌ Query failed"
        kubectl describe query $QUERY_NAME -n $NAMESPACE
        exit 1
    fi
    
    echo -n "."
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

echo ""

if [ "$PHASE" != "done" ]; then
    echo "⚠️  Query did not complete within timeout"
    kubectl describe query $QUERY_NAME -n $NAMESPACE
    exit 1
fi

echo ""
echo "=== Step 9: View Results ==="

echo "Fetching agent responses..."

RESPONSES=$(kubectl get query $QUERY_NAME -n $NAMESPACE -o jsonpath='{.status.responses}')

# Save to repo root
REPO_ROOT="$(git rev-parse --show-toplevel)"
RESULTS_JSON="${REPO_ROOT}/pr-${PR_NUMBER}-review.json"
RESULTS_MD="${REPO_ROOT}/pr-${PR_NUMBER}-review.md"

echo "$RESPONSES" | jq . > "$RESULTS_JSON"

# Extract Markdown content from agents
CODE_QUALITY=$(echo "$RESPONSES" | jq -r '.[0].raw' | jq -r '.[0].content' 2>/dev/null || echo "")
FUNCTIONALITY=$(echo "$RESPONSES" | jq -r '.[0].raw' | jq -r '.[1].content' 2>/dev/null || echo "")

# Create readable Markdown file
{
  echo "# PR #${PR_NUMBER} AI Review"
  echo "**Repository**: ${REPO}"
  echo "**Branch**: ${BRANCH_NAME}"
  echo "**Review ID**: ${REVIEW_ID}"
  echo ""
  echo "---"
  echo ""
  echo "$CODE_QUALITY"
  echo ""
  echo "---"
  echo ""
  echo "$FUNCTIONALITY"
} > "$RESULTS_MD"

echo ""
echo "✅ Review complete!"
echo "   JSON: ${RESULTS_JSON}"
echo "   Markdown: ${RESULTS_MD}"
echo ""

echo "=== Code Quality Review ==="
echo "$CODE_QUALITY" | head -30

echo ""
echo "=== Functionality Analysis ==="
echo "$FUNCTIONALITY" | head -30

echo ""
echo "=== Summary ==="
echo "Repository: $REPO"
echo "PR: #$PR_NUMBER"
echo "Review ID: $REVIEW_ID"
echo "Query: $QUERY_NAME"
echo "Status: $PHASE"
echo ""
echo "Full results: ${RESULTS_FILE}"
echo "Service logs: /tmp/ark-pr-reviewer.log"
echo ""
echo "To view service logs:"
echo "  tail -f /tmp/ark-pr-reviewer.log"
echo ""
echo "To cleanup:"
echo "  kubectl delete query $QUERY_NAME -n $NAMESPACE"
echo "  kubectl delete namespace $NAMESPACE"
if [ -n "$SERVICE_PID" ]; then
    echo "  kill $SERVICE_PID  # Stop the service"
fi

