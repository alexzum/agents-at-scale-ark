# ARK Banking Demo - CI/CD Deployment Guide

This guide explains how to deploy the ARK banking demo in a cloud environment using CI/CD pipelines, adapting the local development approach for production-ready deployments.

## **Overview**

The core principle remains the same as local development:
1. **Manage secrets** securely through cloud providers
2. **Deploy resources** using `kubectl apply -f demo-resources/banking-demo-all.yaml`
3. **Automate** the process through CI/CD pipelines

---

## **Key Differences from Local Development**

| Aspect | Local Development | Cloud CI/CD |
|--------|------------------|-------------|
| **Secrets** | `.ark.env` file | Cloud secret management |
| **Cluster Auth** | Local kubeconfig | Service accounts/tokens |
| **Deployment** | Manual commands | Automated pipelines |
| **Environment** | Single cluster | Multiple environments |

---

## **1. Secret Management**

### **Cloud Provider Examples**

**GitHub Actions:**
```yaml
env:
  ARK_QUICKSTART_API_KEY: ${{ secrets.AZURE_OPENAI_API_KEY }}
  ARK_QUICKSTART_BASE_URL: ${{ secrets.AZURE_OPENAI_BASE_URL }}
  ARK_QUICKSTART_API_VERSION: "2024-04-01-preview"
  ARK_QUICKSTART_MODEL_VERSION: "gpt-35-turbo"
```

**GitLab CI:**
```yaml
variables:
  ARK_QUICKSTART_API_KEY: $AZURE_OPENAI_API_KEY
  ARK_QUICKSTART_BASE_URL: $AZURE_OPENAI_BASE_URL
  ARK_QUICKSTART_API_VERSION: "2024-04-01-preview"
  ARK_QUICKSTART_MODEL_VERSION: "gpt-35-turbo"
```

**Azure DevOps:**
```yaml
variables:
- name: ARK_QUICKSTART_API_KEY
  value: $(AZURE_OPENAI_API_KEY)
- name: ARK_QUICKSTART_BASE_URL
  value: $(AZURE_OPENAI_BASE_URL)
```

---

## **2. Cluster Authentication**

### **GitHub Actions**
```yaml
- name: Configure kubectl
  uses: azure/k8s-set-context@v1
  with:
    method: kubeconfig
    kubeconfig: ${{ secrets.KUBE_CONFIG }}
```

### **GitLab CI**
```yaml
before_script:
  - echo "$KUBE_CONFIG" | base64 -d > kubeconfig
  - export KUBECONFIG=kubeconfig
```

### **Azure DevOps**
```yaml
- task: Kubernetes@1
  inputs:
    connectionType: 'Kubernetes Service Connection'
    kubernetesServiceEndpoint: 'your-k8s-connection'
```

---

## **3. Deployment Pipeline Examples**

### **GitHub Actions Complete Pipeline**

```yaml
name: Deploy ARK Banking Demo
on:
  push:
    paths:
      - 'demo-resources/**'
    branches:
      - main
  workflow_dispatch:

jobs:
  deploy-demo:
    runs-on: ubuntu-latest
    environment: production
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Configure kubectl
      uses: azure/k8s-set-context@v1
      with:
        method: kubeconfig
        kubeconfig: ${{ secrets.KUBE_CONFIG }}
    
    - name: Create namespace if needed
      run: kubectl create namespace demo-bank --dry-run=client -o yaml | kubectl apply -f -
    
    - name: Create/update secrets
      env:
        API_KEY: ${{ secrets.AZURE_OPENAI_API_KEY }}
        BASE_URL: ${{ secrets.AZURE_OPENAI_BASE_URL }}
      run: |
        kubectl create secret generic demo-bank-secrets \
          --namespace=demo-bank \
          --from-literal=api-key="$API_KEY" \
          --from-literal=base-url="$BASE_URL" \
          --from-literal=api-version="2024-04-01-preview" \
          --from-literal=model-version="gpt-35-turbo" \
          --dry-run=client -o yaml | kubectl apply -f -
    
    - name: Deploy demo resources
      run: kubectl apply -f demo-resources/banking-demo-all.yaml
    
    - name: Wait for agents to be ready
      run: kubectl wait --for=condition=Available agent --all -n demo-bank --timeout=300s
    
    - name: Verify deployment
      run: |
        echo "Checking agent status..."
        kubectl get agents -n demo-bank
        echo "Checking model status..."
        kubectl get models -n demo-bank
```

### **GitLab CI Pipeline**

```yaml
stages:
  - deploy
  - verify

variables:
  KUBECTL_VERSION: "1.28.0"

before_script:
  - curl -LO "https://dl.k8s.io/release/v${KUBECTL_VERSION}/bin/linux/amd64/kubectl"
  - chmod +x kubectl && mv kubectl /usr/local/bin/
  - echo "$KUBE_CONFIG" | base64 -d > kubeconfig
  - export KUBECONFIG=kubeconfig

deploy-demo:
  stage: deploy
  script:
    - kubectl create namespace demo-bank --dry-run=client -o yaml | kubectl apply -f -
    - |
      kubectl create secret generic demo-bank-secrets \
        --namespace=demo-bank \
        --from-literal=api-key="$AZURE_OPENAI_API_KEY" \
        --from-literal=base-url="$AZURE_OPENAI_BASE_URL" \
        --from-literal=api-version="2024-04-01-preview" \
        --from-literal=model-version="gpt-35-turbo" \
        --dry-run=client -o yaml | kubectl apply -f -
    - kubectl apply -f demo-resources/banking-demo-all.yaml
  only:
    changes:
      - demo-resources/**

verify-deployment:
  stage: verify
  script:
    - kubectl wait --for=condition=Available agent --all -n demo-bank --timeout=300s
    - kubectl get agents -n demo-bank
    - kubectl get models -n demo-bank
  only:
    changes:
      - demo-resources/**
```

---

## **4. Multi-Environment Setup**

### **Environment-Specific Configurations**

**Structure:**
```
demo-resources/
├── base/
│   ├── banking-demo-all.yaml
│   └── agents/
├── environments/
│   ├── dev/
│   │   └── kustomization.yaml
│   ├── staging/
│   │   └── kustomization.yaml
│   └── prod/
│       └── kustomization.yaml
```

**Example Kustomization (staging):**
```yaml
# demo-resources/environments/staging/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: demo-bank-staging

resources:
- ../../base

patchesStrategicMerge:
- |-
  apiVersion: ark.mckinsey.com/v1alpha1
  kind: Model
  metadata:
    name: default
  spec:
    config:
      azure:
        baseUrl:
          value: "https://staging-azure.example.com"
```

**Deployment Command:**
```bash
kubectl apply -k demo-resources/environments/staging/
```

---

## **5. Advanced Pipeline Features**

### **Blue/Green Deployment**
```yaml
- name: Blue/Green Deployment
  run: |
    # Deploy to blue environment
    kubectl apply -f demo-resources/banking-demo-all.yaml -l version=blue
    
    # Wait and verify
    kubectl wait --for=condition=Available agent --all -l version=blue --timeout=300s
    
    # Switch traffic to blue
    kubectl patch service demo-service -p '{"spec":{"selector":{"version":"blue"}}}'
    
    # Clean up green
    kubectl delete agents,models -l version=green
```

### **Rollback Strategy**
```yaml
- name: Rollback on failure
  if: failure()
  run: |
    echo "Deployment failed, rolling back..."
    kubectl rollout undo deployment/agent-deployment -n demo-bank
    kubectl get agents -n demo-bank
```

### **Slack Notifications**
```yaml
- name: Notify on deployment
  if: always()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    channel: '#ark-deployments'
    text: 'ARK Banking Demo deployment ${{ job.status }} in demo-bank namespace'
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

---

## **6. Security Best Practices**

### **Secret Management**
- ✅ Store API keys in cloud secret management (never in code)
- ✅ Use environment-specific secrets
- ✅ Rotate secrets regularly
- ✅ Limit secret access with RBAC

### **Cluster Access**
- ✅ Use service accounts instead of personal kubeconfigs
- ✅ Implement least-privilege RBAC
- ✅ Enable audit logging
- ✅ Use network policies

### **Pipeline Security**
- ✅ Require approval for production deployments
- ✅ Use branch protection rules
- ✅ Scan container images for vulnerabilities
- ✅ Implement deployment gates

---

## **7. Monitoring and Observability**

### **Health Checks**
```bash
# Add to pipeline for monitoring
kubectl get agents -n demo-bank -o json | jq '.items[] | {name: .metadata.name, available: .status.conditions[0].status}'
```

### **Logging Integration**
```yaml
- name: Collect logs on failure
  if: failure()
  run: |
    kubectl logs -l app=ark-agent -n demo-bank --tail=100 > agent-logs.txt
    kubectl describe agents -n demo-bank > agent-status.txt
```

---

## **8. Benefits of CI/CD Approach**

✅ **GitOps Ready**: Changes to `demo-resources/*` automatically trigger deployments  
✅ **Environment Promotion**: Same manifests work across dev/staging/prod  
✅ **Audit Trail**: All changes tracked in git history  
✅ **Rollback Capability**: Easy to revert to previous versions  
✅ **Scalable**: Works for multiple environments/clusters  
✅ **Consistent**: Eliminates manual deployment errors  
✅ **Secure**: Proper secret management and access control  

---

## **Quick Start**

1. **Store secrets** in your CI/CD platform
2. **Configure cluster access** with service accounts
3. **Copy pipeline template** for your platform
4. **Commit changes** to `demo-resources/*`
5. **Watch automated deployment** 🚀

The core deployment remains the same - just edit `demo-resources/*` files and the pipeline handles the rest!
