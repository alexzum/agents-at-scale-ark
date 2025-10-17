# Local Development Setup for ARK PR Reviewer

Test the PR review system on your local machine without AWS infrastructure.

## Prerequisites

- Docker Desktop with Kubernetes enabled OR minikube/kind
- kubectl configured
- Helm 3
- Node.js and npm (for Husky testing)
- ARK already installed locally (or follow ARK quickstart)

## Quick Start

### 1. Ensure ARK is Running Locally

```bash
# If ARK is not installed yet:
npm install -g @agents-at-scale/ark
ark install

# Verify ARK is running
kubectl get pods -n ark-system
ark status
```

### 2. Create Local Namespace

```bash
kubectl create namespace ark-pr-review
```

### 3. Create Secrets

Create a file `local-secrets.env`:

```bash
# GitHub PAT (needs repo read access)
GITHUB_TOKEN=ghp_your_github_token_here

# Jira (optional for local testing - can skip)
JIRA_BASE_URL=https://jira.company.com
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your_jira_token

# Azure OpenAI (or use ARK's default model)
AZURE_OPENAI_BASE_URL=https://your-instance.openai.azure.com
AZURE_OPENAI_API_KEY=your_key_here
```

Apply secrets:

```bash
kubectl create secret generic ark-pr-reviewer-secrets \
  --from-env-file=local-secrets.env \
  --namespace=ark-pr-review
```

### 4. Deploy ARK Resources (Agents, Team, Model)

```bash
# Deploy model (using existing model or create new)
kubectl apply -f k8s/model.yaml

# Deploy agents
kubectl apply -f k8s/agent-code-quality.yaml
kubectl apply -f k8s/agent-functionality.yaml

# Deploy team
kubectl apply -f k8s/team-pr-review.yaml

# Verify resources
kubectl get agents,teams,models -n ark-pr-review
```

### 5. Run Service Locally (Development Mode)

```bash
# Install dependencies
make init

# Create local .env file
cp .env.example .env

# Edit .env with your values:
# - GITHUB_TOKEN
# - JIRA settings (or set JIRA_FALLBACK_ENABLED=true to skip)
# - AWS settings can be dummy values for local
# - Set KUBERNETES_NAMESPACE=ark-pr-review

# Run service
make dev
```

The service will start on `http://localhost:8080`

### 6. Test with a Real PR

Open a new terminal:

```bash
# Test the service is running
curl http://localhost:8080/health

# Trigger a review for a real PR
curl -X POST http://localhost:8080/review/pr \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "mckinsey/agents-at-scale-ark",
    "pr_number": 123,
    "branch_name": "PROJ-456-feature",
    "commit_sha": "abc123"
  }'
```

### 7. Monitor Progress

```bash
# Watch queries being created and completed
kubectl get queries -n ark-pr-review -w

# Check query status
kubectl describe query pr-123-xxxxx -n ark-pr-review

# View service logs
# (in the terminal where you ran 'make dev')
```

## Local Testing Workflow

### Option 1: Test Against Historical PRs

```bash
# List recent closed PRs
gh pr list --repo mckinsey/agents-at-scale-ark --state closed --limit 5

# Pick a PR number and test
curl -X POST http://localhost:8080/review/pr \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "mckinsey/agents-at-scale-ark",
    "pr_number": <PR_NUMBER>,
    "branch_name": "PROJ-000-test",
    "commit_sha": null
  }'
```

### Option 2: Test With Your Own Test PR

1. Create a test branch:
```bash
git checkout -b PROJ-000-test-pr-review
echo "# Test" >> TEST.md
git add TEST.md
git commit -m "test: add test file"
git push origin PROJ-000-test-pr-review
```

2. Create PR on GitHub

3. Trigger review:
```bash
curl -X POST http://localhost:8080/review/pr \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "mckinsey/agents-at-scale-ark",
    "pr_number": <YOUR_PR_NUMBER>,
    "branch_name": "PROJ-000-test-pr-review"
  }'
```

## Local Configuration Without AWS

### Skip S3 Logging

For local testing, reviews are logged to stdout. To enable local file logging:

Edit `ark_pr_reviewer/s3_logger.py` to write to local files:

```python
# Add this method to S3Logger class
async def log_review_local(self, review: PRReviewResult) -> str:
    """Log review to local file instead of S3"""
    import os
    from pathlib import Path
    
    log_dir = Path("./review-logs") / review.repository / str(review.pr_number)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"{review.review_id}.json"
    log_file.write_text(review.model_dump_json(indent=2))
    
    return str(log_file)
```

Then update `api.py` to use `log_review_local` instead of `log_review`.

### Skip Jira Integration

Set in your `.env`:

```bash
JIRA_FALLBACK_ENABLED=true
JIRA_BASE_URL=http://localhost
JIRA_USERNAME=test
JIRA_API_TOKEN=test
```

The service will gracefully skip Jira validation and only do code quality review.

## Viewing Results

### Check Query Status

```bash
# Get the query name from service logs
QUERY_NAME=pr-123-1234567890

# View query details
kubectl get query $QUERY_NAME -n ark-pr-review -o yaml

# Check responses
kubectl get query $QUERY_NAME -n ark-pr-review -o jsonpath='{.status.responses}' | jq .
```

### Extract Agent Findings

```bash
# Get code quality findings
kubectl get query $QUERY_NAME -n ark-pr-review \
  -o jsonpath='{.status.responses[0].content}' | jq .

# Get functionality analysis
kubectl get query $QUERY_NAME -n ark-pr-review \
  -o jsonpath='{.status.responses[1].content}' | jq .
```

## Troubleshooting

### Service Can't Create Queries

Check RBAC permissions:

```bash
kubectl apply -f - <<EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: ark-pr-reviewer-role
  namespace: ark-pr-review
rules:
  - apiGroups: ["ark.mckinsey.com"]
    resources: ["queries"]
    verbs: ["create", "get", "list", "watch"]
  - apiGroups: ["ark.mckinsey.com"]
    resources: ["queries/status"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ark-pr-reviewer-binding
  namespace: ark-pr-review
subjects:
  - kind: User
    name: system:serviceaccount:default:default
roleRef:
  kind: Role
  name: ark-pr-reviewer-role
  apiGroup: rbac.authorization.k8s.io
EOF
```

### Agents Not Responding

Check agent and model status:

```bash
kubectl get agents,models -n ark-pr-review
kubectl describe agent code-quality-reviewer -n ark-pr-review
kubectl describe model review-model -n ark-pr-review
```

### GitHub API Rate Limits

If testing frequently, you may hit rate limits. Check:

```bash
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/rate_limit
```

## Testing Branch Validation

### Test Husky Hook Locally

```bash
# Install husky
npm install

# Try pushing with invalid branch name
git checkout -b invalid-branch-name
git commit --allow-empty -m "test"
git push origin invalid-branch-name
# Should be blocked by Husky

# Try with valid branch name
git checkout -b PROJ-000-valid-test
git push origin PROJ-000-valid-test
# Should succeed
```

### Test GitHub Actions Locally

Use [act](https://github.com/nektos/act) to test workflows locally:

```bash
# Install act
brew install act  # or appropriate package manager

# Test branch validation workflow
act pull_request -W .github/workflows/validate_branch_name_jira.yml
```

## Performance Testing

Test with multiple PRs concurrently:

```bash
# Create test script
cat > test-concurrent.sh <<'EOF'
#!/bin/bash
for i in {1..5}; do
  curl -X POST http://localhost:8080/review/pr \
    -H "Content-Type: application/json" \
    -d "{\"repository\":\"mckinsey/agents-at-scale-ark\",\"pr_number\":$i,\"branch_name\":\"PROJ-000-test\"}" &
done
wait
EOF

chmod +x test-concurrent.sh
./test-concurrent.sh
```

Watch queries:

```bash
kubectl get queries -n ark-pr-review -w
```

## Cleanup

```bash
# Delete namespace and all resources
kubectl delete namespace ark-pr-review

# Remove test branches
git branch -D PROJ-000-test-pr-review
git push origin --delete PROJ-000-test-pr-review
```

## Next Steps

Once local testing is successful:

1. Review agent prompts and tune based on results
2. Test with last 5 closed PRs (Phase 1 testing)
3. Deploy to AWS using main deployment guide
4. Enable GitHub Actions workflow

## Tips

- Start with `JIRA_FALLBACK_ENABLED=true` to focus on code quality agent first
- Use `LOG_LEVEL=DEBUG` for verbose logging
- Test with small PRs first (few files changed)
- Check agent responses are valid JSON before processing
- Monitor token usage if using paid model API

