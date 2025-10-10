# Smart Customer Support with AI Quality Gates - Demo Setup

This directory contains all the resources needed to run the example workflow for the Medium article.

## Quick Start

### 1. Deploy ARK Resources

```bash
# From the ark-oss root directory
kubectl apply -f services/n8n/article/01-agent.yaml
kubectl apply -f services/n8n/article/02-evaluator.yaml

# Wait for resources to be ready
kubectl wait --for=condition=ready agent/support-agent --timeout=60s
kubectl wait --for=condition=ready evaluator/support-quality-evaluator --timeout=60s
```

### 2. Import n8n Workflow

1. Open n8n: http://n8n.default.127.0.0.1.nip.io:8080
2. Click "+" to create new workflow
3. Click the three dots (⋯) in top-right
4. Select "Import from File"
5. Choose `n8n-workflow.json`
6. Configure credentials:
   - **ARK API**: Use `http://ark-api.default.svc.cluster.local` as base URL
   - **Slack API** (optional): Add your Slack webhook/token

### 3. Test the Workflow

#### Test Data (High Quality Response Expected)

```bash
curl -X POST http://n8n.default.127.0.0.1.nip.io:8080/webhook/customer-support \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Alice Johnson",
    "customer_email": "alice@example.com",
    "account_type": "Enterprise",
    "priority": "high",
    "issue": "I cannot access the API dashboard. When I try to log in, I get a 403 error. I have verified my credentials are correct."
  }'
```

**Expected Result**: Quality score ≥ 0.8 → Auto-sent to customer ✅

#### Test Data (Low Quality Response Expected)

```bash
curl -X POST http://n8n.default.127.0.0.1.nip.io:8080/webhook/customer-support \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Bob Smith",
    "customer_email": "bob@example.com",
    "account_type": "Free",
    "priority": "low",
    "issue": "Why is everything broken?"
  }'
```

**Expected Result**: Vague question may result in lower score → Queued for review ⚠️

## Workflow Overview

```
Webhook Trigger
    ↓
ARK Agent (support-agent)
    ↓ (generates response)
ARK Evaluation (support-quality-evaluator)
    ↓ (scores: relevance, accuracy, clarity, usefulness, compliance)
IF: Score >= 0.8
    ├─ TRUE → Send to Customer → Slack Notify
    └─ FALSE → Add to Review Queue → Slack Alert
```

## Key Features Demonstrated

### 1. ARK Agent Node
- **Agent Selection**: Choose from dropdown of available agents
- **Input Mapping**: Use expressions to compose context-rich prompts
- **Wait Mode**: Synchronous execution with timeout

### 2. ARK Evaluation Node
- **Evaluation Type**: Direct (input/output evaluation)
- **Evaluator Selection**: Choose from dropdown of available evaluators
- **Advanced Parameters**:
  - `scope`: Multi-dimensional quality assessment
  - `minScore`: Threshold for quality gates
  - `temperature`: Evaluation consistency (0.1 = strict)
  - `context`: Additional evaluation criteria

### 3. Quality-Based Routing
- **Decision Point**: IF node checks evaluation score
- **High Quality Path**: Auto-send + notify team
- **Low Quality Path**: Queue for review + alert supervisor

## Screenshots to Capture

For the article, please capture:

### 1. n8n Workflow Canvas
- **Full workflow view** showing all nodes connected
- **Highlight**: ARK Agent and ARK Evaluation nodes

### 2. ARK Agent Node Configuration
- **Agent dropdown** showing available agents
- **Input field** with expression mapping
- **Wait settings** configured

### 3. ARK Evaluation Node Configuration
- **Evaluator dropdown** showing available evaluators
- **Input/Output fields** mapped from previous nodes
- **Advanced Parameters section**:
  - Scope multi-select: relevance, accuracy, clarity, usefulness, compliance
  - Min Score: 0.8
  - Temperature: 0.1
  - Context field filled

### 4. Workflow Execution (High Quality)
- **Execution view** showing green success path
- **ARK Evaluation output** showing:
  - `status.score`: 0.92 (or similar high score)
  - `status.passed`: true
  - `status.message`: Evaluation reasoning
- **IF node** taking TRUE branch
- **Final response** to webhook

### 5. Workflow Execution (Low Quality)
- **Execution view** showing review path
- **ARK Evaluation output** showing:
  - `status.score`: 0.65 (or similar low score)
  - `status.passed`: false
  - `status.message`: Explanation of issues
- **IF node** taking FALSE branch
- **Review queue** notification

### 6. ARK Resources in Kubernetes
```bash
# Screenshot these commands and their output:
kubectl get agent,model,evaluator
kubectl describe agent support-agent
kubectl describe evaluator support-quality-evaluator
```

### 7. Evaluation Details
```bash
# After running the workflow, show evaluation results:
kubectl get evaluation -l evaluator=support-quality-evaluator
kubectl describe evaluation <evaluation-name>
```

## Troubleshooting

### Agent not found
```bash
kubectl get agent support-agent
# If not ready, check logs:
kubectl logs -n ark-system deployment/ark-controller-manager
```

### Evaluator not available
```bash
kubectl get evaluator support-quality-evaluator
# Check if model is ready:
kubectl get model default
```

### n8n cannot connect to ARK API
- Ensure ARK API credentials use: `http://ark-api.default.svc.cluster.local`
- Check ARK API is running: `kubectl get svc ark-api`

### Webhook not responding
- Check workflow is active (toggle in n8n UI)
- Verify webhook path: `http://n8n.default.127.0.0.1.nip.io:8080/webhook/customer-support`

## Next Steps

After capturing screenshots, you can:
1. Modify agent instructions to change response style
2. Adjust evaluation scope to focus on specific qualities
3. Change min_score threshold to see different routing
4. Add more conditions (e.g., route by priority or account type)
5. Integrate with real systems (CRM, ticketing, email)

## Clean Up

```bash
kubectl delete -f services/n8n/article/
```
