# n8n + ARK Quick Start Guide

Get up and running with n8n and ARK in minutes.

## Prerequisites

- Kubernetes cluster with ARK installed (`make quickstart`)
- kubectl configured
- Helm 3 installed

## Installation

### 1. Install n8n

```bash
make n8n-install
```

This will:
- Deploy n8n to your cluster
- Create persistent storage for workflows
- Set up HTTPRoute for access via localhost-gateway
- Configure ARK API URL

### 2. Access n8n UI

```bash
# View all routes
make routes

# n8n will be available at:
# http://n8n.default.127.0.0.1.nip.io:8080
```

Open your browser to the n8n URL.

### 3. Import Sample Workflow

1. In n8n UI, click **Workflows** (left sidebar)
2. Click **Import from File**
3. Select file: `samples/n8n-workflows/ark-agent-query-basic.json`
4. Click **Import**
5. Click **Save**

### 4. Execute Workflow

1. Click the **Execute Workflow** button (play icon)
2. Watch as each node executes
3. View results in the execution panel
4. Inspect the agent's response

## Testing the Execute Endpoint

Test the new ARK API endpoint directly:

```bash
# List available agents
curl http://ark-api.default.127.0.0.1.nip.io:8080/v1/agents

# Execute an agent query
curl -X POST http://ark-api.default.127.0.0.1.nip.io:8080/v1/agents/YOUR_AGENT_NAME/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hello, what can you help me with?",
    "wait": true,
    "timeout": "60s"
  }'
```

Replace `YOUR_AGENT_NAME` with an actual agent from the list.

## Next Steps

### Create Your Own Workflow

1. In n8n, click **+ New Workflow**
2. Add a **Manual Trigger** node
3. Add an **HTTP Request** node:
   - Method: POST
   - URL: `http://ark-api.default.svc.cluster.local:8000/v1/agents/YOUR_AGENT/execute`
   - Body: JSON with `{"input": "your query", "wait": true}`
4. Add a **Code** node to process the response
5. Execute and test!

### Enable Webhook Trigger

Import the webhook workflow:

```bash
# In n8n UI:
# Workflows → Import from File → samples/n8n-workflows/ark-agent-query-with-params.json
```

Test the webhook:

```bash
curl -X POST http://n8n.default.127.0.0.1.nip.io:8080/webhook/ark-agent-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "YOUR_AGENT_NAME",
    "input": "What is 2+2?",
    "timeout": "30s"
  }'
```

### Build Complex Workflows

Try these patterns:

**Sequential Agent Chain:**
```
Trigger → Execute Agent 1 → Extract Response → Execute Agent 2 → Combine Results
```

**Parallel Agent Queries:**
```
Trigger → Split → Execute Multiple Agents (parallel) → Merge Responses
```

**Conditional Routing:**
```
Execute Agent → IF Node → Route A (success) / Route B (error)
```

## Troubleshooting

### n8n Pod Not Starting

```bash
# Check pod status
kubectl get pods -n default -l app=n8n

# View logs
kubectl logs -n default -l app=n8n -f
```

### Cannot Access n8n UI

```bash
# Check HTTPRoute
kubectl get httproute -n default n8n-route

# Verify localhost-gateway is running
kubectl get pods -n ark-system -l app.kubernetes.io/name=nginx-gateway-fabric
```

### ARK API Connection Failed

```bash
# Test from n8n pod
kubectl exec -n default deployment/n8n -- wget -O- http://ark-api.default.svc.cluster.local:8000/health

# Should return: {"status":"healthy","service":"ark-api"}
```

### Workflow Execution Timeout

Increase timeout in both places:
1. HTTP Request node: Options → Timeout (milliseconds)
2. Execute request body: `"timeout": "300s"`

## Uninstall

```bash
make n8n-uninstall
```

## Documentation

- Full integration docs: [docs/content/integrations/n8n.mdx](docs/content/integrations/n8n.mdx)
- Detailed specification: [SPECIFICATION_N8N_INTEGRATION.md](SPECIFICATION_N8N_INTEGRATION.md)
- ARK API reference: [docs/content/reference/ark-apis.mdx](docs/content/reference/ark-apis.mdx)
- Sample workflows: [samples/n8n-workflows/](samples/n8n-workflows/)

## Support

For issues or questions:
- Check the [n8n integration docs](docs/content/integrations/n8n.mdx)
- Review sample workflows in `samples/n8n-workflows/`
- Consult the full specification in `SPECIFICATION_N8N_INTEGRATION.md`

## What's Next?

- [ ] Build custom n8n community node package
- [ ] Add webhook callbacks for async queries
- [ ] Enable streaming responses
- [ ] Add authentication support
- [ ] Create more workflow templates

Enjoy building agentic workflows with n8n and ARK!
