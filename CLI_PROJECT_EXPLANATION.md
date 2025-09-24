# ARK CLI Project Creation - Explanation

This document explains what "Create an ARK project using the CLI" means in the context of ARK and provides clarification for the demo setup.

---

## **What is an "ARK Project"?**

In the context of ARK, a "project" refers to a **collection of related AI agents, teams, tools, and configurations** that work together to solve a business problem. It's similar to how you might have a "microservices project" with multiple services.

### **ARK Project Structure**
```
banking-demo-project/
├── agents/
│   ├── inquiry-router.yaml
│   ├── account-helper.yaml
│   └── loan-advisor.yaml
├── teams/
│   └── customer-service-team.yaml
├── models/
│   └── banking-model.yaml
├── tools/
│   └── account-lookup-tool.yaml
└── README.md
```

---

## **CLI Project Creation Options**

### **Option 1: File-Based Project (Current Approach)**
Since ARK doesn't have a dedicated `ark init` command (like `npm init`), creating a project means:

1. **Creating directory structure** for organizing resources
2. **Writing YAML definitions** for agents, teams, models
3. **Version controlling** these definitions in Git
4. **Deploying** via `kubectl apply`

```bash
# Create project structure
mkdir banking-demo-project
cd banking-demo-project

mkdir -p {agents,teams,models,tools,docs}

# Create resource definitions
# (This is what our demo does)
```

### **Option 2: Namespace-Based Project (Demo Approach)**
Our demo uses Kubernetes namespaces as project boundaries:

```bash
# Create project namespace
kubectl create namespace demo-bank

# Deploy project resources to namespace
kubectl apply -f demo-resources/ -n demo-bank

# All project resources are isolated in this namespace
```

---

## **ARK vs Other CLI Tools**

### **Traditional Project CLIs**
```bash
# Node.js
npm init my-project
cd my-project
npm install

# Python
poetry new my-project
cd my-project
poetry install

# React
npx create-react-app my-app
```

### **ARK Approach**
```bash
# ARK (Current - Manual)
mkdir my-ark-project
cd my-ark-project
# Create YAML files
kubectl apply -f . -n my-project-namespace

# ARK (Potential Future)
# ark init banking-demo --template=customer-service
# ark deploy --namespace=demo-bank
```

---

## **What Our Demo Actually Does**

### **Step 1: Project Structure Creation**
```bash
# In our demo, we create:
demo-resources/
├── agents/
│   ├── inquiry-router.yaml
│   ├── account-helper.yaml
│   └── loan-advisor.yaml
├── teams/
│   └── customer-service-team.yaml
└── models/
    └── demo-model.yaml
```

### **Step 2: Project Deployment**
```bash
# Create project namespace
kubectl create namespace demo-bank

# Deploy entire project
kubectl apply -f demo-resources/ -n demo-bank
```

### **Step 3: Project Management**
```bash
# List project resources
kubectl get all -n demo-bank

# Update project
kubectl apply -f demo-resources/ -n demo-bank

# Delete project
kubectl delete namespace demo-bank
```

---

## **Version Control Integration**

### **Git Workflow for ARK Projects**
```bash
# Initialize project repository
git init banking-demo-project
cd banking-demo-project

# Add ARK resources
git add agents/ teams/ models/
git commit -m "Initial ARK project structure"

# Create feature branch for new agent
git checkout -b feature/fraud-detection-agent

# Add new agent
cat > agents/fraud-detector.yaml << EOF
apiVersion: ark.mckinsey.com/v1alpha1
kind: Agent
metadata:
  name: fraud-detector
spec:
  prompt: "You detect fraudulent transactions..."
EOF

git add agents/fraud-detector.yaml
git commit -m "feat: add fraud detection agent"

# Merge to main
git checkout main
git merge feature/fraud-detection-agent

# Deploy updated project
kubectl apply -f . -n demo-bank
```

---

## **Project Lifecycle Management**

### **Development Workflow**
1. **Local Development**
   ```bash
   # Edit YAML files locally
   vim agents/account-helper.yaml
   
   # Test locally
   kubectl apply -f agents/account-helper.yaml -n demo-bank
   fark agent account-helper "test query"
   ```

2. **Version Control**
   ```bash
   git add agents/account-helper.yaml
   git commit -m "improve account helper prompts"
   git push origin main
   ```

3. **Deployment**
   ```bash
   # Manual deployment
   kubectl apply -f . -n demo-bank
   
   # Or CI/CD deployment (GitOps)
   # ArgoCD, Flux, etc. watch the repo and auto-deploy
   ```

### **Environment Management**
```bash
# Development environment
kubectl apply -f . -n banking-dev

# Staging environment  
kubectl apply -f . -n banking-staging

# Production environment
kubectl apply -f . -n banking-prod
```

---

## **ARK Project Best Practices**

### **1. Directory Structure**
```
my-ark-project/
├── agents/           # Individual agent definitions
├── teams/            # Team workflow definitions
├── models/           # Model configurations
├── tools/            # Custom tools and MCPs
├── evaluations/      # Quality gates and tests
├── docs/             # Project documentation
└── deploy/           # Deployment configurations
    ├── dev/
    ├── staging/
    └── prod/
```

### **2. Naming Conventions**
```yaml
# Use consistent naming
metadata:
  name: banking-account-helper    # project-function-type
  namespace: banking-demo         # project-environment
  labels:
    project: banking-demo
    component: customer-service
    version: v1.0.0
```

### **3. Configuration Management**
```bash
# Use ConfigMaps for environment-specific settings
kubectl create configmap banking-config \
  --from-literal=bank-name="Regional Trust Bank" \
  --from-literal=support-email="support@regionaltrust.com"
```

---

## **Summary for Demo Context**

**What we're actually doing in the demo:**

1. ✅ **Creating project structure** → `demo-resources/` directory with YAML files
2. ✅ **Version control ready** → All files can be committed to Git
3. ✅ **Namespace isolation** → `demo-bank` namespace as project boundary
4. ✅ **Resource deployment** → `kubectl apply -f demo-resources/`
5. ✅ **Project management** → Standard Kubernetes resource lifecycle

**This approach demonstrates:**
- Enterprise-grade resource organization
- GitOps-ready deployment patterns  
- Proper Kubernetes project isolation
- Scalable multi-environment workflows

The demo effectively shows how ARK projects are created and managed, even without a dedicated `ark init` CLI command.
