# PR Review Sample - Deployment Fix

## Issues Identified

1. **Agents and Team Not Registered**: YAML files existed in the sample directory but were not deployed to Kubernetes
2. **Service Not Exposed as Tool**: The PR review service was not accessible to other ARK agents
3. **Missing Deployment Instructions**: Users didn't know they needed to `kubectl apply` the resources

## Fixes Applied

### 1. Created Kustomization for Easy Deployment

**File**: `samples/pr-review-team/kustomization.yaml`

Enables one-command deployment of all resources:
```bash
kubectl apply -k samples/pr-review-team/
```

Includes:
- Namespace creation
- Agent deployments
- Team deployment
- Tool registration

### 2. Created Tool Resource

**File**: `samples/pr-review-team/tool-pr-review.yaml`

Exposes the PR review service as an ARK Tool, allowing other agents to trigger reviews:

```yaml
apiVersion: ark.mckinsey.com/v1alpha1
kind: Tool
metadata:
  name: pr-review
  namespace: ark-pr-review
spec:
  type: http
  description: "Triggers an AI-powered pull request review..."
  http:
    url: "http://ark-pr-reviewer.ark-pr-review.svc.cluster.local:8080/review/pr"
    method: POST
    timeout: 300s
```

**Usage by other agents:**
```yaml
apiVersion: ark.mckinsey.com/v1alpha1
kind: Agent
metadata:
  name: release-manager
spec:
  tools:
    - type: custom
      name: pr-review
      namespace: ark-pr-review
```

### 3. Created Namespace Manifest

**File**: `samples/pr-review-team/namespace.yaml`

Ensures the `ark-pr-review` namespace is created with proper labels.

### 4. Updated Documentation

**Updated files:**
- `samples/pr-review-team/README.md` - Added deployment instructions with kustomize
- `docs/content/user-guide/samples/pr-review-team/index.mdx` - Added deployment step with verification
- `docs/content/user-guide/samples/pr-review-team/architecture.mdx` - Added Tool resource documentation

**Key additions:**
- Clear "Deploy ARK Resources" section
- kubectl apply -k command
- Verification steps showing expected output
- Explanation of what gets deployed
- Tool usage examples

## How to Deploy

### Quick Start
```bash
cd samples/pr-review-team

# Deploy all resources
kubectl apply -k .

# Verify deployment
kubectl get agents,teams,tools -n ark-pr-review
```

### Expected Output
```
NAME                                            MODEL     AVAILABLE   AGE
agent.ark.mckinsey.com/code-quality-reviewer    default   True        10s
agent.ark.mckinsey.com/functionality-analyzer   default   True        10s

NAME                                   AGE
team.ark.mckinsey.com/pr-review-team   10s

NAME                            AGE
tool.ark.mckinsey.com/pr-review 10s
```

### Manual Deployment
```bash
# Create namespace
kubectl create namespace ark-pr-review

# Deploy agents
kubectl apply -f agents/

# Deploy team
kubectl apply -f teams/

# Deploy tool
kubectl apply -f tool-pr-review.yaml
```

## Benefits

1. **Proper ARK Integration**: Resources are now registered in ARK and visible via `kubectl get`
2. **Reusable by Other Agents**: Any agent can trigger PR reviews via the tool
3. **Single Command Deployment**: `kubectl apply -k .` deploys everything
4. **Clear Verification**: Users can verify all resources are deployed correctly
5. **Follows ARK Patterns**: Consistent with other samples like `walkthrough`

## Tool Integration Example

Create an agent that can trigger PR reviews:

```yaml
apiVersion: ark.mckinsey.com/v1alpha1
kind: Agent
metadata:
  name: dev-assistant
  namespace: default
spec:
  prompt: |
    You are a development assistant that helps developers with their workflow.
    You can trigger PR reviews when requested.
  modelRef:
    name: default
  tools:
    - type: custom
      name: pr-review
      namespace: ark-pr-review
```

Query example:
```yaml
apiVersion: ark.mckinsey.com/v1alpha1
kind: Query
metadata:
  name: review-my-pr
spec:
  input: "Please review PR #320 in mckinsey/agents-at-scale-ark"
  targets:
    - type: agent
      name: dev-assistant
```

The agent will:
1. Understand the request to review a PR
2. Invoke the `pr-review` tool with appropriate parameters
3. Return the results to the user

## Verification

Test the deployment:

```bash
# Deploy
kubectl apply -k samples/pr-review-team/

# Check agents are registered
kubectl get agents -n ark-pr-review
# Should show: code-quality-reviewer, functionality-analyzer

# Check team is registered
kubectl get teams -n ark-pr-review
# Should show: pr-review-team

# Check tool is registered
kubectl get tools -n ark-pr-review
# Should show: pr-review

# Check agents are AVAILABLE
kubectl get agents -n ark-pr-review -o wide
# Status should show "True" for AVAILABLE column
```

## Date
October 17, 2025
