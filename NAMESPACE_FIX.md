# PR Review Sample - Namespace Configuration Fix

## Issue

The ARK Dashboard UI dropdown only showed "default" namespace, preventing users from seeing PR review resources deployed to the `ark-pr-review` namespace.

## Root Cause

The ARK Dashboard service account (`ark-dashboard-sa`) runs in the `default` namespace and only has permissions to list resources in that namespace. It does not have cluster-wide (ClusterRole) permissions to view resources across all namespaces.

## Solution

Changed the PR review sample to deploy resources to the `default` namespace instead of `ark-pr-review`.

### Changes Made

1. **Updated kustomization.yaml**
   - Changed `namespace: ark-pr-review` to `namespace: default`
   - Removed `namespace.yaml` resource (no longer needed)

2. **Updated All Resource Manifests**
   - `agents/code-quality-reviewer.yaml` - namespace: default
   - `agents/functionality-analyzer.yaml` - namespace: default
   - `teams/pr-review-team.yaml` - namespace: default
   - `tool-pr-review.yaml` - namespace: default

3. **Updated Tool Service URL**
   - Changed from `ark-pr-reviewer.ark-pr-review.svc.cluster.local`
   - To `ark-pr-reviewer.default.svc.cluster.local`

4. **Updated local-test.sh**
   - Changed `NAMESPACE="ark-pr-review"` to `NAMESPACE="default"`

5. **Updated Documentation**
   - README.md - Added explanation of why default namespace is used
   - index.mdx - Updated deployment instructions
   - Added note about Dashboard visibility

## Benefits

### ✅ Immediate Dashboard Visibility
Resources are now visible in the ARK Dashboard UI without requiring additional RBAC configuration:

```
Dashboard → Select "default" namespace → See:
- code-quality-reviewer agent
- functionality-analyzer agent  
- pr-review-team team
- pr-review tool
```

### ✅ Simpler Setup for Samples
Users don't need to:
- Configure ClusterRole permissions for Dashboard
- Switch namespaces in kubectl
- Remember to specify `-n ark-pr-review` in commands

### ✅ Consistent with Other Samples
Most ARK samples deploy to the `default` namespace for ease of use.

## Verification

```bash
# Deploy resources
cd samples/pr-review-team
kubectl apply -k .

# Verify in default namespace
kubectl get agents,teams,tools -n default | grep -E "pr-review|code-quality|functionality"
```

Output:
```
NAME                                            MODEL     AVAILABLE   AGE
agent.ark.mckinsey.com/code-quality-reviewer    default   True        10s
agent.ark.mckinsey.com/functionality-analyzer   default   True        10s

NAME                                   AGE
team.ark.mckinsey.com/pr-review-team   10s

NAME                              AGE
tool.ark.mckinsey.com/pr-review   10s
```

## Alternative Solution (Not Implemented)

For production deployments requiring namespace isolation, you could:

1. Create a ClusterRole for the Dashboard:
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: ark-dashboard-viewer
rules:
  - apiGroups: ["ark.mckinsey.com"]
    resources: ["agents", "teams", "tools", "queries", "models"]
    verbs: ["get", "list", "watch"]
```

2. Create a ClusterRoleBinding:
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: ark-dashboard-viewer-binding
subjects:
  - kind: ServiceAccount
    name: ark-dashboard-sa
    namespace: default
roleRef:
  kind: ClusterRole
  name: ark-dashboard-viewer
  apiGroup: rbac.authorization.k8s.io
```

However, for **samples**, using the `default` namespace is the better choice for simplicity and immediate usability.

## Production Deployment Consideration

If you deploy the actual PR review service (not just the sample) to production, consider:

1. **Using a dedicated namespace** with appropriate RBAC
2. **Updating the Dashboard** to have multi-namespace viewing capability
3. **Configuring network policies** for namespace isolation
4. **Setting resource quotas** per namespace

For the **sample demonstration**, `default` namespace provides the best user experience.

## Date
October 17, 2025
