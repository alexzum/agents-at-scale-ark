# ARK Banking Demo - Execution Guide

This guide provides the exact commands to run the ARK banking demo as outlined in `DEMO_STORYLINE.md`.

## **Prerequisites**

- ARK cluster running with `devspace dev`
- `fark` CLI installed and available
- `kubectl` configured and working
- Demo should take ~15 minutes total

---

## **Part 1: Environment Setup (2 minutes)**

### **Step 1: Setup Demo Environment**
```bash
# Create secrets from .ark.env (standalone approach)
./demo-resources/setup-demo-secrets.sh

# This script will:
# - Create demo-bank namespace if it doesn't exist
# - Load values from .ark.env
# - Create demo-bank-secrets with API key, base URL, etc.
# - Make the demo completely standalone
```

### **Step 2: Deploy Agents**
```bash
# Option 1: Deploy everything at once (recommended)
kubectl apply -f demo-resources/banking-demo-all.yaml

# Option 2: Deploy individual resources
# kubectl apply -f demo-resources/agents/
# kubectl apply -f demo-resources/teams/
# kubectl apply -f demo-resources/model-and-rbac.yaml

# Set context to demo namespace for convenience
kubectl config set-context --current --namespace=demo-bank

# Wait for agents to be ready
kubectl get agents -w
# Wait until all show AVAILABLE: True (about 30 seconds)
```

---

## **Part 2: Individual Agent Demo (5 minutes)**

### **Step 3: Test Inquiry Router Agent**
```bash
# Test classification capability
echo "🔍 Testing Inquiry Router Agent"
fark agent inquiry-router "What's my account balance?"

echo "🔍 Testing mixed request classification"
fark agent inquiry-router "I want to check my balance and learn about loans"
```

### **Step 4: Test Account Helper Agent**
```bash
# Test account information
echo "💰 Testing Account Helper Agent"
fark agent account-helper "What's my current account balance?"

fark agent account-helper "Show me my recent transactions"
```

### **Step 5: Test Loan Advisor Agent**
```bash
# Test loan information
echo "🏠 Testing Loan Advisor Agent"
fark agent loan-advisor "What loan products do you offer?"

fark agent loan-advisor "What are your current mortgage rates?"
```

---

## **Part 3: Team Workflow Demo (5 minutes)**

### **Step 6: Verify Team Deployment**
```bash
# Team should already be deployed from banking-demo-all.yaml
# Verify team is ready
kubectl get teams
```

### **Step 7: Demonstrate Team Coordination**
```bash
# Main demo scenario - mixed request
echo "🏦 MAIN DEMO: Customer Service Team Workflow"
echo "Customer Request: What's my account balance and what loans do you offer?"

fark team customer-service-team "What's my account balance and what loans do you offer?"

# Show team execution details
kubectl get queries --sort-by=.metadata.creationTimestamp | tail -1
```

### **Step 8: Additional Team Scenarios** 
```bash
# Pure account request (should route to Account Helper only)
echo "📊 Testing account-only request"
fark team customer-service-team "Can you tell me my current account balance?"

# Pure loan request (should route to Loan Advisor only)  
echo "💳 Testing loan-only request"
fark team customer-service-team "What are your personal loan rates?"

# Complex mixed request
echo "🔄 Testing complex mixed request"
fark team customer-service-team "I need my account status and want to apply for a mortgage"
```

---

## **Part 4: API Integration Demo (2 minutes)**

### **Step 9: REST API Endpoints**
```bash
# Test agent endpoint via API
echo "🌐 Testing Agent API Endpoints"

# Query individual agent via REST API (correct format)
curl -s -X POST "http://localhost:8000/v1/namespaces/demo-bank/queries" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "demo-agent-query",
    "input": "What is my account balance?",
    "targets": [
      {
        "type": "agent",
        "name": "account-helper"
      }
    ]
  }' | jq '.name'

# Wait for completion and get result
sleep 3
curl -s "http://localhost:8000/v1/namespaces/demo-bank/queries/demo-agent-query" | jq '.status.responses[0].content'

echo

# Query team via REST API (correct format)
curl -s -X POST "http://localhost:8000/v1/namespaces/demo-bank/queries" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "demo-team-query", 
    "input": "I need my balance and loan information",
    "targets": [
      {
        "type": "team",
        "name": "customer-service-team"
      }
    ]
  }' | jq '.name'

# Wait for team completion and get result (teams take longer)
sleep 8
curl -s "http://localhost:8000/v1/namespaces/demo-bank/queries/demo-team-query" | jq '.status.responses[0].content'

echo

# Check query history via API
curl "http://localhost:8000/v1/namespaces/demo-bank/queries" | jq '.items[0:3]'
```

### **Step 10: System Status via API**
```bash
# Check all agents status
echo "📊 System Status via API"
curl -s "http://localhost:8000/v1/namespaces/demo-bank/agents" | jq '.items[] | {name: .name, available: .available}'

# Check team status
curl -s "http://localhost:8000/v1/namespaces/demo-bank/teams" | jq '.items[] | {name: .name, strategy: .strategy, members_count: .members_count}'
```

---

## **Part 5: Observability Quick Look (1 minute)**

### **Step 11: Monitoring & Metrics**
```bash
# Check recent events
echo "📈 Recent ARK Events"
kubectl get events --sort-by=.lastTimestamp | tail -10

# Check query performance
echo "⚡ Query Performance Metrics"
kubectl get queries -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.duration}{"\n"}{end}' | tail -5

# Show Langfuse integration (if available)
echo "🔍 Observability Dashboard"
echo "View detailed traces at: http://localhost:3000/traces"
echo "AI-specific metrics available in Langfuse integration"
```

---

## **Part 6: Cleanup (Optional)**

### **Step 12: Demo Cleanup**
```bash
# Remove demo resources
kubectl delete namespace demo-bank

# Reset kubectl context to default
kubectl config set-context --current --namespace=default

echo "✅ Demo cleanup complete"
```

---

## **Refreshing Demo Secrets**

When your `.ark.env` file changes (e.g., daily token updates), refresh the demo easily:

```bash
# Update secrets from latest .ark.env
./demo-resources/setup-demo-secrets.sh

# The script automatically:
# - Loads new values from .ark.env
# - Updates the demo-bank-secrets
# - Triggers model restart to pick up new values
# - No need to redeploy agents/teams

# Verify agents pick up new credentials
kubectl get agents -w
# Wait for agents to show AVAILABLE: True
```

---

## **Demo Script Notes**

### **Key Talking Points During Demo**

**Setup Phase**:
- "We're creating an isolated namespace - this shows proper Kubernetes resource management"
- "These agents deploy just like any other microservice"

**Individual Agents**:
- "Each agent is specialized - Router for classification, Account Helper for account queries, Loan Advisor for loan information"
- "Notice the sub-second response times"

**Team Workflow**:
- "This is where ARK shines - coordinating multiple agents in a workflow"
- "The customer gets one comprehensive response, but multiple AI agents collaborated"

**API Integration**:
- "Your existing systems can integrate via these REST APIs"
- "This is how LegacyX or any other system would call ARK agents"

**Observability**:
- "Full request tracing and monitoring - you can see exactly what each agent did"
- "This integrates with your existing monitoring infrastructure"

### **Expected Response Times**
- Individual agent queries: 200-500ms
- Team queries: 800ms-2s (sequential execution)
- API responses: Similar to CLI times

### **Troubleshooting Quick Fixes**
```bash
# If agents show as not available
kubectl describe agent <agent-name> -n demo-bank

# If team queries fail
kubectl describe team customer-service-team -n demo-bank

# Force restart if needed
kubectl rollout restart deployment -l app=ark -n demo-bank
```

This guide provides a complete, runnable demo that showcases ARK's enterprise capabilities in a banking context.
