# AI-Powered PR Review Sample

This sample demonstrates how to use ARK agents to automatically review pull requests, providing code quality analysis and Jira ticket alignment validation.

## What This Sample Demonstrates

- **Multi-Agent Team**: Two specialized agents working together via sequential strategy
- **External API Integration**: GitHub API for PR data and Jira REST API for requirements
- **Custom Service**: FastAPI service orchestrating ARK agents
- **GitHub Actions Integration**: Automated PR review workflow
- **Markdown Output**: Clean, readable reviews ready for Jira comments

## Quick Start

### Prerequisites

- ARK installed and running (`descpace dev` from repo root)
- GitHub personal access token
- Jira API credentials (optional, for ticket validation)
- kubectl access to your cluster

### 1. Deploy ARK Resources

The sample deploys to the `default` namespace so resources are immediately visible in the ARK Dashboard.

```bash
cd samples/pr-review-team

# Deploy all ARK resources (agents, team, tool) to default namespace
kubectl apply -k .

# Verify deployment
kubectl get agents,teams,tools -n default | grep -E "pr-review|code-quality|functionality"
```

**Expected output:**
```
NAME                                            MODEL     AVAILABLE   AGE
agent.ark.mckinsey.com/code-quality-reviewer    default   True        10s
agent.ark.mckinsey.com/functionality-analyzer   default   True        10s

NAME                                   AGE
team.ark.mckinsey.com/pr-review-team   10s

NAME                              AGE
tool.ark.mckinsey.com/pr-review   10s
```

### 2. Test Locally

```bash
cd service

# Create .env file with your credentials
cat > .env << EOF
GITHUB_TOKEN=ghp_your_token_here
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_USERNAME=your.email@company.com
JIRA_API_TOKEN=your_jira_token
API_PORT=8081
EOF

# Run test against a PR
./local-test.sh owner/repo PR_NUMBER

# View results
cat ../../pr-PR_NUMBER-review.md
```

### 3. Deploy Service to Kubernetes (Production)

For production use, deploy the FastAPI orchestration service to Kubernetes:

```bash
# Install service via Helm
helm install ark-pr-reviewer ./chart \
  --namespace default \
  --set config.githubToken=$GITHUB_TOKEN \
  --set config.jiraBaseUrl=https://your-company.atlassian.net \
  --set config.jiraUsername=your.email@company.com \
  --set config.jiraApiToken=$JIRA_API_TOKEN
```

**Note**: The ARK resources (agents, team, tool) from Step 1 are already deployed to Kubernetes and are required. Step 3 deploys the **service component** that orchestrates reviews, which can alternatively run:
- Locally for testing (Step 2)
- On any server accessible to GitHub Actions
- In Kubernetes (this step) for production

## Components

### Agents

- **code-quality-reviewer**: Analyzes code for security, patterns, complexity, and adherence to project standards
- **functionality-analyzer**: Validates PR changes against Jira ticket requirements

See [`agents/`](./agents/) for agent definitions.

### Team

- **pr-review-team**: Sequential team that executes both agents one after another (code quality first, then functionality analysis)

See [`teams/`](./teams/) for team configuration.

**Note**: ARK does not currently support true parallel agent execution. The supported strategies are `sequential`, `round-robin`, `selector`, and `graph`. For PR reviews, sequential execution works well since both agents analyze the same PR data.

### Tool

- **pr-review**: HTTP tool that exposes the PR review service API, allowing other ARK agents to trigger PR reviews programmatically

See [`tool-pr-review.yaml`](./tool-pr-review.yaml) for tool definition.

**Usage example with another agent:**
```yaml
apiVersion: ark.mckinsey.com/v1alpha1
kind: Agent
metadata:
  name: release-manager
  namespace: default
spec:
  prompt: "You help manage releases and can trigger PR reviews."
  modelRef:
    name: default
  tools:
    - type: custom
      name: pr-review  # References pr-review tool in same namespace
```

### Service

FastAPI service that:
1. Receives PR review requests via API
2. Fetches PR details from GitHub
3. Fetches Jira ticket details (if available)
4. Creates ARK Query to execute agents
5. Returns Markdown-formatted results

See [`service/`](./service/) for service code and local testing.

### Infrastructure

Terraform configurations for deploying ARK and the PR reviewer service to AWS EKS.

See [`infrastructure/`](./infrastructure/) for deployment instructions.

### GitHub Workflows

Example GitHub Actions workflows for:
- Automated PR review on PR events
- Branch naming validation

See [`github-workflows/`](./github-workflows/) for examples.

**Note**: This repository uses these workflows actively in [`.github/workflows/`](../../.github/workflows/).

## Documentation

For complete documentation, see:

- **Full Tutorial**: [User Guide - PR Review Sample](../../docs/content/user-guide/samples/pr-review-team/index.mdx)
- **Architecture**: [Architecture Documentation](../../docs/content/user-guide/samples/pr-review-team/architecture.mdx)
- **Service README**: [service/README.md](./service/README.md)

## Repository-Wide Integration

This sample integrates with repository-wide standards:

- **Branch Naming Convention**: Enforced via [`.husky/pre-push`](../../.husky/pre-push) and [`.github/workflows/validate_branch_name_jira.yml`](../../.github/workflows/validate_branch_name_jira.yml)
- **Conventional Commits**: Required format documented in [`CONTRIBUTING.md`](../../CONTRIBUTING.md)
- **Active PR Review**: [`.github/workflows/pr_review_ai.yml`](../../.github/workflows/pr_review_ai.yml) runs on all PRs

## Sample Output

```markdown
# Code Quality Review

## Summary
The PR follows project standards with minor suggestions...

## Findings

### 🔴 Critical
- None found

### 🟡 Medium
- **File**: `samples/example/service.py:42`
- **Issue**: Missing error handling for API call
- **Suggestion**: Add try/except block with appropriate error handling

# Functionality Analysis

## Jira Integration
**Jira Ticket Available**: ✅ Yes

## Alignment Assessment
**Overall Alignment**: ✅ Good

## ✅ Covered Requirements
- Requirement 1: Implemented in commit abc123
- Requirement 2: Added in file service.py

## ❌ Missing Requirements
- None
```

## Customization

### Modify Agent Prompts

Edit the agent YAML files in [`agents/`](./agents/) to customize:
- Code quality checks and severity thresholds
- Jira requirement validation logic
- Output format and structure

### Change Team Strategy

Edit [`teams/pr-review-team.yaml`](./teams/pr-review-team.yaml) to:
- Adjust `maxTurns` for agent iterations
- Add more agents to the team
- Change team strategy (sequential, selector, graph)

### Update Service Logic

Edit Python code in [`service/src/ark_pr_reviewer/`](./service/src/ark_pr_reviewer/) to:
- Add new API integrations
- Customize query generation
- Modify response formatting

## Testing

```bash
# Test agent deployment
kubectl apply -f agents/
kubectl get agents -n default | grep -E "code-quality|functionality"

# Test team deployment  
kubectl apply -f teams/
kubectl get teams -n default | grep pr-review

# Test tool deployment
kubectl apply -f tool-pr-review.yaml
kubectl get tools -n default | grep pr-review

# Test local service
cd service
./local-test.sh mckinsey/agents-at-scale-ark 320
```

## Support

For questions or issues:
1. Check the [documentation](../../docs/content/user-guide/samples/pr-review-team/index.mdx)
2. Review service logs: `tail -f /tmp/ark-pr-reviewer.log` (local) or `kubectl logs -n default deployment/ark-pr-reviewer` (K8s)
3. Check ARK query status: `kubectl get queries -n default`
4. View resources in Dashboard: Select `default` namespace in the UI dropdown

## License

This sample is part of the ARK project. See [LICENSE](../../LICENSE) for details.

