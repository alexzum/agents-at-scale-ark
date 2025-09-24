# ARK-KYC demo 

This document provides a guide to the organization of ARK sample configurations and file locations.

## 📁 Directory of samples necessary for demo
```
samples/
├── evaluator/                    # Central evaluator definitions
├── evaluators/                   # Legacy evaluator files
├── models/                      # Model configurations
├── kyc-demo-gpt4-RAG/           # GPT-4.1-mini demonstrations
├── kyc-demo-ollama-rag/         # Local Ollama model demonstrations
│   ├── gemma2-2b/               # Gemma2 model demos
│   ├── mistral-7b/              # Mistral model demos
│   ├── qwen-8b/                 # Qwen model demos
│   └── smollm2-135m/            # SmolLM2 model demos
└── kyc-demo-ark-v4-tools/       # Advanced ARK v4 with tools
```

## 🔧 Configuration Directories

### **`models/`** - Model Configurations
```
models/
├── default.yaml                     # Default GPT-4.1-mini with AI Gateway config (update instance ID)
├── text-embedding-ada-002.yaml      # Azure OpenAI embeddings
├── local-ollama-gemma2-2b.yaml
├── local-ollama-mistral-7b.yaml
├── local-ollama-smollm2135.yaml
├── local-ollama.yaml (references qwen-8b model)
└── [other model configurations]
```

### **`evaluator/`** - Centralized Evaluator Definitions
```
evaluator/
├── kyc-context-quality-evaluator-v4.yaml    # RAG quality assessment
├── kyc-event-based-evaluator.yaml           # Workflow execution assessment
├── kyc-llm-metrics-evaluator-v4.yaml        # Performance monitoring
└── [other evaluator files (irrelevant)]
```

## 🎯 Core KYC Demonstration Folders

### **`kyc-demo-gpt4-RAG/`**
```
kyc-demo-gpt4-RAG/
├── agents/
│   ├── planner-agent.yaml
│   └── risk-officer-rag-agent.yaml
├── teams/
│   └── kyc-context-enhanced-team.yaml
├── kyc-query-gpt4.1-mini.yaml
├── kyc-eval-event-gpt4.1-mini.yaml
├── kyc-eval-metrics-gpt4.1-mini.yaml
└── kyc-eval-contextRAG-gpt4.1-mini.yaml
```

### **`kyc-demo-ollama-rag/`**

#### **`gemma2-2b/`**
```
gemma2-2b/
├── agents/
│   ├── planner-agent-gemma2.yaml
│   └── risk-officer-rag-agent-gemma2.yaml
├── teams/
│   └── kyc-context-enhanced-team-gemma2.yaml
├── kyc-query-gemma2-2bn.yaml
├── kyc-eval-event-gemma2-2bn.yaml
├── kyc-eval-metrics-gemma2-2bn.yaml
└── kyc-eval-contextRAG-gemma2-2bn.yaml
```

#### **`mistral-7b/`**
```
mistral-7b/
├── agents/
│   ├── planner-agent-mistral.yaml
│   └── risk-officer-rag-agent-mistral.yaml
├── teams/
│   └── kyc-context-enhanced-team-mistral.yaml
├── kyc-query-mistral.yaml
├── kyc-eval-event-mistral.yaml
├── kyc-eval-metrics-mistral.yaml
└── kyc-eval-contextRAG-mistral.yaml
```

#### **`qwen-8b/`**
```
qwen-8b/
├── agents/
│   ├── planner-agent-ollama.yaml
│   └── risk-officer-rag-agent-ollama.yaml
├── teams/
│   └── kyc-context-enhanced-team-ollama.yaml
├── kyc-query-qwen-8b.yaml
├── kyc-eval-event-qwen-8b.yaml
├── kyc-eval-metrics-qwen-8b.yaml
└── kyc-eval-contextRAG-qwen-8b.yaml
```

#### **`smollm2-135m/`**
```
smollm2-135m/
├── agents/
│   ├── planner-agent-ollama.yaml
│   └── risk-officer-rag-agent-ollama.yaml
├── teams/
│   └── kyc-context-enhanced-team-ollama.yaml
├── kyc-query-smollm2.yaml
├── kyc-eval-event-smollm2.yaml
├── kyc-eval-metrics-smollm2.yaml
└── kyc-eval-contextRAG-smollm2-v2.yaml
```

## 🎬 Preparing for Demo Day

### Pre-requisites
- **Familiarity with basic kubectl commands/k9**
- **Necessary deployments should already be running in minikube** with status 1/1:
  - `ark-api-devspace` or `ark-api`
  - `ark-dashboard-devspace` or `ark-dashboard`
  - `ark-evaluator`
  - `executor-langchain`
- **Default model configured**: Default model is pre-configured in `samples/models/default.yaml` with GPT-4.1-mini and AI Gateway settings
  - **⚠️ Important**: Update the `baseUrl` instance ID in `default.yaml` to match your AI Gateway instance

### Running Query

#### Step 1: Patch Token
Go to AI gateway, copy the 12-hour JWT token and patch it:

```bash
NEW_TOKEN="x.x.x"

kubectl patch secret azure-openai-secret -n default --type='json' -p="[{\"op\": \"replace\", \"path\": \"/data/token\", \"value\": \"$(echo -n $NEW_TOKEN | base64)\"}]"
```

#### Step 2: Restart Services
**Why restart both services?** The hybrid RAG architecture requires coordination between two services:
- **ARK Controller**: Manages query orchestration and caches Azure OpenAI tokens for efficiency
- **Executor-langchain**: Performs actual RAG operations and reads tokens from environment variables

Both services must be restarted because:
- Controller needs restart to clear its token cache
- Executor reads environment variables only at pod startup time
- Without both restarts, RAG operations will fail with authentication errors

Execute these steps to ensure both services pick up the new Azure OpenAI token:

```bash
# 1. Restart ARK Controller (to clear token cache)
kubectl rollout restart deployment ark-controller-devspace -n ark-system

# 2. Restart Executor-langchain (to pick up new environment variable)
kubectl rollout restart deployment executor-langchain

# 3. Wait for pods to be ready
kubectl rollout status deployment ark-controller-devspace -n ark-system --timeout=60s
kubectl rollout status deployment executor-langchain --timeout=60s

# 4. Verify the new token is loaded
# Get the new executor pod name
kubectl get pods | grep executor-langchain

# Check that the new token is in the environment (will show first/last few chars)
kubectl exec <new-pod-name> -- sh -c 'echo ${AZURE_OPENAI_API_KEY:0:8}...${AZURE_OPENAI_API_KEY: -4}'
```

#### Step 3: Run Demo
Once things are ready:

1. **Run your query**
2. **Wait some time** (monitor with `kubectl get query <query-name> -w`)
3. **Run your evaluations** (after query shows "done")

## 🚀 Usage

### Deploy Evaluators
```bash
kubectl apply -f samples/evaluator/
```

### Deploy Complete Demos

#### **GPT-4.1-mini Demo Deployment**
```bash
# 1. Deploy evaluators first
kubectl apply -f samples/evaluator/

# 2. Deploy supporting resources first
kubectl apply -f samples/kyc-demo-gpt4-RAG/agents/
kubectl apply -f samples/kyc-demo-gpt4-RAG/teams/

# 3. Deploy query
kubectl apply -f samples/kyc-demo-gpt4-RAG/kyc-query-gpt4.1-mini.yaml

# 4. Wait for query to complete (IMPORTANT!)
kubectl get query kyc-context-enhanced-query-gpt4.1-mini -w
# Wait until PHASE shows "done" before proceeding

# 5. Then deploy evaluations
kubectl apply -f samples/kyc-demo-gpt4-RAG/kyc-eval-*.yaml
```

#### **Qwen-8B Demo Deployment**
```bash
# 1. Deploy evaluators first (if not already done)
kubectl apply -f samples/evaluator/

# 2. Deploy supporting resources first
kubectl apply -f samples/kyc-demo-ollama-rag/qwen-8b/agents/
kubectl apply -f samples/kyc-demo-ollama-rag/qwen-8b/teams/

# 3. Deploy query
kubectl apply -f samples/kyc-demo-ollama-rag/qwen-8b/kyc-query-qwen-8b.yaml

# 4. Wait for query to complete (IMPORTANT!)
kubectl get query kyc-context-enhanced-query-qwen-8b -w
# Wait until PHASE shows "done" before proceeding
# Note: Qwen-8B takes ~4-5 minutes due to model size

# 5. Then deploy evaluations
kubectl apply -f samples/kyc-demo-ollama-rag/qwen-8b/kyc-eval-*.yaml
```

#### **Mistral-7B Demo Deployment**
```bash
# 1. Deploy evaluators first (if not already done)
kubectl apply -f samples/evaluator/

# 2. Deploy supporting resources first
kubectl apply -f samples/kyc-demo-ollama-rag/mistral-7b/agents/
kubectl apply -f samples/kyc-demo-ollama-rag/mistral-7b/teams/

# 3. Deploy query
kubectl apply -f samples/kyc-demo-ollama-rag/mistral-7b/kyc-query-mistral.yaml

# 4. Wait for query to complete (IMPORTANT!)
kubectl get query kyc-context-enhanced-query-mistral -w
# Wait until PHASE shows "done" before proceeding
# Note: Mistral-7B takes ~45-60 seconds

# 5. Then deploy evaluations
kubectl apply -f samples/kyc-demo-ollama-rag/mistral-7b/kyc-eval-*.yaml
```

### Performance Expectations

| Model | Execution Time | Event Score | Metrics Score | Context Score | Cost |
|-------|----------------|-------------|---------------|---------------|------|
| **GPT-4.1-mini** | ~31s | 100% ✅ | 77% ✅ | 90% ✅ | ~$0.28 |
| **Qwen-8B** | ~4m20s | 90% ✅ | 64% ❌* | 90% ✅ | ~$0.000 |
| **Mistral-7B** | ~45s | 100% ✅ | 96% ✅ | 90% ✅ | ~$0.000 |

*Metrics score failure due to execution time exceeding 120s threshold

## ⚠️ Limitations of Demo

### **Tool Calls Not Available in Main Demos**

The primary KYC demonstrations (GPT-4.1-mini, Qwen-8B, Mistral-7B) have the following limitations:

#### **1. No Tool Call Demonstrations**
- **Issue**: Our main demo agents run on `executor-langchain`, not the native ARK execution engine
- **Impact**: Tool calls cannot be demonstrated during the standard demo flow
- **Architecture**: `executor-langchain` is specialized for RAG operations only

#### **2. RAG-Only Execution**
- **Current capability**: `executor-langchain` can only perform Retrieval-Augmented Generation (RAG)
- **Demo strategy**: Use voice-over during demos to explain that event evaluations can capture tool calls
- **Note**: The evaluation system itself supports tool call monitoring, but the execution engine used in main demos does not

#### **3. Tool Call Demo Workaround**
If clients insist on seeing tool calls in action, redirect to specialized samples:

**For OpenAI models:**
```
samples/kyc-demo-ark-v4-tools/openai/
```

**For local Ollama models:**
```
samples/kyc-demo-ark-v4-tools/local/
```

**Requirements for tool call demos:**
- MCP (Model Context Protocol) server setup required
- Follow deployment guide: [ARK User Guide - Deploy Complete Workflow](https://mckinsey.github.io/agents-at-scale-ark/user-guide/samples/walkthrough/#:~:text=monitoring%20and%20validation-,Deploy%20the%20Complete%20Workflow,-First%2C%20set%20up)
- Additional deployment of `get_current_date` function (to be added later by Muhammad)

### **Demo Strategy**
1. **Focus on RAG capabilities** in main demos (retrieval quality, hybrid architecture, cost optimization)
2. **Mention tool call support** via voice-over during event evaluation section
3. **Reference tool call samples** if specifically requested by clients
4. **Emphasize evaluation system** can monitor and validate tool executions

### Check Status commands
```bash
# Check all resource types
kubectl get evaluators
kubectl get queries
kubectl get evaluations

# Monitor specific query progress
kubectl get query <query-name> -w

# Check query details
kubectl describe query <query-name>

# View evaluation results
kubectl get evaluations -o wide
kubectl describe evaluation <evaluation-name>
```

### Troubleshooting

#### Debug Commands:
```bash
# Check pod logs (this will help with checking chunking)
kubectl logs deployment/executor-langchain --tail=50

# Check ARK controller logs
kubectl logs deployment/ark-controller-devspace -n ark-system --tail=50

# Verify token is loaded
kubectl get pods | grep executor-langchain
kubectl exec <pod-name> -- sh -c 'echo ${AZURE_OPENAI_API_KEY:0:8}...${AZURE_OPENAI_API_KEY: -4}'

```