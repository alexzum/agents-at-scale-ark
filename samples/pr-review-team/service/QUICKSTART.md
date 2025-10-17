# ARK PR Reviewer - Quick Start Guide

## 🚀 Local Testing (5 minutes)

### 1. Setup
```bash
cd services/ark-pr-reviewer

# Install dependencies
make init

# Configure credentials
cp .env.local.example .env
nano .env  # Add your GitHub token and Jira credentials
```

### 2. Required Configuration in `.env`
```bash
GITHUB_TOKEN=ghp_your_github_token_here
JIRA_BASE_URL=https://company.atlassian.net
JIRA_USERNAME=your.email@company.com
JIRA_API_TOKEN=your_jira_token
API_PORT=8081  # Change if 8080 is taken
```

### 3. Test a PR
```bash
./local-test.sh mckinsey/agents-at-scale-ark 320
```

### 4. View Results
```bash
# Readable Markdown (copy to Jira!)
cat ../../pr-320-review.md

# Raw JSON (for processing)
cat ../../pr-320-review.json

# Service logs
tail -f /tmp/ark-pr-reviewer.log
```

## 📋 Output Format

### Clean Markdown ✅
```markdown
# Code Quality Review

## Findings

### 🔴 Critical
- **File**: `path/to/file.go:42`
- **Issue**: Security vulnerability
- **Suggestion**: Fix with XYZ

### 🟡 Medium
[Medium findings...]
```

### Ready for Jira
Just copy the Markdown file content directly into Jira comments - it renders beautifully!

## 🔧 Troubleshooting

### Port 8080 already in use?
```bash
# Change port in .env
API_PORT=8081
```

### Service won't start?
```bash
# Check logs
tail -f /tmp/ark-pr-reviewer.log

# Kill existing service
pkill -f "uvicorn ark_pr_reviewer.api:app"
```

### Jira not connecting?
```bash
# Test Jira connection
curl -u "$JIRA_USERNAME:$JIRA_API_TOKEN" \
  "$JIRA_BASE_URL/rest/api/2/issue/ARKQB-376"
```

## 📊 What Gets Analyzed

### Code Quality Agent
- ✅ Security vulnerabilities
- ✅ Code complexity
- ✅ Error handling
- ✅ Pattern adherence (CLAUDE.md)
- ✅ Test coverage

### Functionality Agent
- ✅ Jira ticket alignment
- ✅ Requirement coverage
- ✅ Out-of-scope changes
- ✅ Breaking changes

## ⚙️ Customization

### Edit Agent Prompts
```bash
nano k8s/agent-code-quality.yaml     # Code quality instructions
nano k8s/agent-functionality.yaml    # Functionality instructions
```

### Change Team Strategy
```bash
nano k8s/team-pr-review.yaml
# Adjust maxTurns or add more agents
```

### Apply Changes
```bash
kubectl apply -f k8s/agent-code-quality.yaml -n ark-pr-review
kubectl apply -f k8s/agent-functionality.yaml -n ark-pr-review
kubectl apply -f k8s/team-pr-review.yaml -n ark-pr-review
```

## 🌐 AWS Deployment (When Ready)

### 1. Provision Infrastructure
```bash
cd ../../infrastructure/pr-review-ark
terraform init
terraform apply
```

### 2. Deploy Service
```bash
cd ../../services/ark-pr-reviewer
helm install ark-pr-reviewer ./chart \
  --namespace ark-pr-review \
  --create-namespace \
  --set config.githubToken=$GITHUB_TOKEN \
  --set config.jiraApiToken=$JIRA_API_TOKEN
```

### 3. Configure GitHub Secrets
In your GitHub repo settings, add:
- `ARK_PR_REVIEW_ENDPOINT` → Service URL
- `ARK_PR_REVIEW_TOKEN` → Auth token

### 4. Enable Workflow
The workflow in `.github/workflows/pr_review_ai.yml` will automatically trigger on PRs.

## 📚 More Documentation

- **Implementation Summary**: `IMPLEMENTATION_SUMMARY.md`
- **Local Setup Guide**: `LOCAL_SETUP.md`
- **Service README**: `README.md`
- **Full Automation Guide**: `../../docs/pr-review-automation.md`

## 🎯 Quick Commands

```bash
# Test a PR
./local-test.sh owner/repo PR_NUMBER

# View last review
cat ../../pr-*-review.md | less

# Check agent status
kubectl get agents -n ark-pr-review

# View queries
kubectl get queries -n ark-pr-review

# Clean up old queries
kubectl delete queries --all -n ark-pr-review

# Restart service
pkill -f "uvicorn ark_pr_reviewer.api:app"
./local-test.sh owner/repo PR_NUMBER

# View service status
curl http://localhost:8081/health
```

## ✨ Tips

1. **Start with recent PRs**: Test on PRs #300+ for better context
2. **Check Jira tickets**: PRs with Jira tickets give better analysis
3. **Review agent prompts**: Customize based on your team's needs
4. **Monitor execution time**: Should be under 60 seconds per PR
5. **Copy Markdown to Jira**: Output is Jira-ready!

---

**Need Help?** Check `IMPLEMENTATION_SUMMARY.md` or service logs at `/tmp/ark-pr-reviewer.log`

