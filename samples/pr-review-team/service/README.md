# ARK PR Reviewer

AI-powered PR review service using ARK agents.

## Overview

FastAPI service that receives PR review requests, fetches PR metadata from GitHub, optionally fetches Jira ticket details, creates ARK Query resources targeting review agents, and logs results to S3.

## Architecture

```
GitHub Actions → ARK PR Reviewer → ARK Team (parallel agents) → S3 Logs
                      ↓
                  GitHub API
                  Jira API
```

## Features

- GitHub API integration for PR metadata
- Jira REST API integration with fallback
- ARK Kubernetes client for creating queries
- S3 logging for review results
- Prometheus metrics
- Async processing with background tasks

## Prerequisites

- Python 3.11+
- uv package manager
- Access to Kubernetes cluster with ARK installed
- AWS credentials for S3 access
- GitHub PAT
- Jira API credentials (optional)

## Development

### Setup

```bash
# Install dependencies
make init

# Copy environment file
cp .env.example .env
# Edit .env with your credentials

# Run locally
make dev
```

### Testing

```bash
# Run tests
make test

# Lint code
make lint
```

## Deployment

### Build Docker image

```bash
make build
```

### Deploy to Kubernetes

See `chart/` directory for Helm chart deployment.

## API Endpoints

### `POST /review/pr`

Initiate a PR review.

**Request:**
```json
{
  "repository": "owner/repo",
  "pr_number": 123,
  "branch_name": "PROJ-456-feature",
  "commit_sha": "abc123"
}
```

**Response:**
```json
{
  "review_id": "uuid",
  "status": "pending",
  "created_at": "2025-10-17T10:30:00Z",
  "message": "Review initiated for PR #123"
}
```

### `GET /review/{review_id}`

Get review results (not yet implemented - check S3).

### `GET /health`

Health check endpoint.

### `GET /metrics`

Prometheus metrics endpoint.

## Configuration

Environment variables:

- `GITHUB_TOKEN` - GitHub PAT for API access
- `JIRA_BASE_URL` - Jira instance URL
- `JIRA_USERNAME` - Jira username
- `JIRA_API_TOKEN` - Jira API token
- `S3_BUCKET` - S3 bucket for review logs
- `KUBERNETES_NAMESPACE` - Namespace for ARK resources
- `TEAM_NAME` - ARK Team resource name

## Review Process

1. Receive PR review request
2. Fetch PR metadata from GitHub
3. Extract Jira ticket from branch name
4. Fetch Jira ticket details (with fallback)
5. Create ARK Query targeting review team
6. Wait for query completion
7. Parse agent responses
8. Log results to S3

## S3 Logging

Reviews are logged to:
```
s3://{bucket}/{prefix}/{repository}/{pr_number}/{review_id}.json
```

Example:
```
s3://ark-pr-review-pr-reviews/reviews/mckinsey/agents-at-scale-ark/123/uuid.json
```

## Metrics

Prometheus metrics exposed at `/metrics`:

- `pr_reviews_total` - Total PR reviews by status
- `pr_review_duration_seconds` - Review duration histogram
- `jira_requests_total` - Jira API requests by status

## Troubleshooting

### Cannot create ARK queries

Check Kubernetes RBAC permissions:
```bash
kubectl auth can-i create queries.ark.mckinsey.com \
  --as system:serviceaccount:ark-pr-review:ark-pr-reviewer
```

### Jira connection fails

Test connectivity from pod:
```bash
kubectl exec -it deployment/ark-pr-reviewer -- curl -I https://jira.company.com
```

### Review logs not appearing in S3

Check IAM role permissions and service account annotations:
```bash
kubectl describe sa ark-pr-reviewer -n ark-pr-review
```

