# Banking Demo Resources

This directory contains all the ARK YAML resources needed for the banking customer service demo.

## **Files Overview**

### **Setup Scripts**
- `setup-demo-secrets.sh` - Creates standalone secrets from .ark.env (run this first!)

### **Individual Agent Files**
- `agents/inquiry-router.yaml` - Classifies customer requests (account, loan, mixed, other)
- `agents/account-helper.yaml` - Handles account balance and transaction inquiries  
- `agents/loan-advisor.yaml` - Provides loan information and rates

### **Team Configuration**
- `teams/customer-service-team.yaml` - Sequential team workflow coordinating all agents

### **Model Configuration**
- `models/default.yaml` - Default model using demo-bank-secrets

### **Infrastructure**
- `model-and-rbac.yaml` - Model configuration and RBAC permissions
- `banking-demo-all.yaml` - Complete demo deployment in single file

## **Quick Deploy**

### **Complete Setup (Recommended)**
```bash
# 1. Create secrets from .ark.env (standalone approach)
./setup-demo-secrets.sh

# 2. Deploy everything (includes model, RBAC, agents, and team)
kubectl apply -f banking-demo-all.yaml

# 3. Set context for convenience
kubectl config set-context --current --namespace=demo-bank
```

### **Alternative: Deploy Individual Resources**
```bash
# Setup secrets
./setup-demo-secrets.sh

# Deploy components separately
kubectl apply -f models/          # Default model
kubectl apply -f model-and-rbac.yaml  # RBAC permissions
kubectl apply -f agents/          # All agents
kubectl apply -f teams/           # Customer service team

# Set context
kubectl config set-context --current --namespace=demo-bank
```

## **Verify Deployment**

```bash
# Check agents are ready (context should be set to demo-bank)
kubectl get agents

# Check team is configured
kubectl get teams

# Wait for all agents to show AVAILABLE: True
kubectl get agents -w
```

## **Test Individual Agents**

```bash
# Test classification
fark agent inquiry-router "What's my balance and what loans do you offer?"

# Test account services
fark agent account-helper "What is my current account balance?"

# Test loan advisory
fark agent loan-advisor "What loan products do you offer?"
```

## **Test Team Workflow**

```bash
# Main demo scenario
fark team customer-service-team "I need my account balance and information about your mortgage loans"
```

## **Refreshing Secrets**

When `.ark.env` changes (e.g., daily token updates):

```bash
# Update secrets from latest .ark.env
./setup-demo-secrets.sh

# Agents will automatically pick up new credentials
kubectl get agents -w  # Wait for AVAILABLE: True
```

## **Cleanup**

```bash
# Remove entire demo
kubectl delete namespace demo-bank

# Reset context
kubectl config set-context --current --namespace=default
```

## **Resource Details**

### **Agent Specifications**
- **Namespace**: `demo-bank`
- **Model**: Uses `default` model (configured in main ARK setup)
- **Labels**: Properly labeled for categorization and filtering
- **Prompts**: Banking-specific with placeholder data for consistent demo results

### **Team Strategy**
- **Type**: Sequential execution (Router → Account Helper → Loan Advisor)
- **Members**: All three agents participate in team workflows
- **Coordination**: Agents can pass context and build comprehensive responses

### **Demo Data**
All agents use consistent placeholder data:
- Account Balance: $2,450.67
- Account Status: Premium Checking, Good Standing
- Loan Rates: Mortgage 6.5%, Personal 8.9%, Auto 5.2%
- Recent Transaction: $150 payment on Dec 20th

This ensures predictable, professional demo results every time.
