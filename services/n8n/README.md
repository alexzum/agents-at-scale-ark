# n8n

Low-code workflow automation with custom ARK nodes.

## Quickstart

```bash
# Show all available recipes.
make help

# Build custom Docker image with ARK nodes
make n8n-build

# Install/uninstall - deploys n8n with ARK nodes to your Kubernetes cluster.
make n8n-install
make n8n-uninstall

# Run tests for custom ARK nodes
make n8n-test

# Access n8n UI
make routes
# Open http://n8n.default.127.0.0.1.nip.io:8080 in your browser
```

## Overview

n8n is a workflow automation platform with custom community nodes for ARK. This integration includes:

### Custom ARK Nodes

- **ARK Agent** - Execute individual ARK agents with input/output handling
- **ARK Model** - Query ARK models directly with prompts and parameters
- **ARK Team** - Coordinate multi-agent workflows with ARK teams
- **ARK Evaluation Trigger** - Webhook trigger for evaluation completion events

### Additional Capabilities

- Build complex agentic workflows with conditional logic
- Chain multiple agents and teams together
- Process and transform responses
- Trigger workflows manually, via webhooks, or on evaluation events

## Architecture

n8n runs as a Kubernetes deployment alongside other ARK services and connects to ARK API to execute agent queries.

## Custom Node Development

Custom ARK nodes are located in `nodes/`:

- `nodes/credentials/` - ARK API credential definition
- `nodes/nodes/ArkAgent/` - ARK Agent node implementation
- `nodes/nodes/ArkModel/` - ARK Model node implementation
- `nodes/nodes/ArkTeam/` - ARK Team node implementation
- `nodes/nodes/ArkEvaluation/` - ARK Evaluation trigger implementation
- `nodes/__tests__/` - Comprehensive test suites (76 tests, >89% coverage)

## Configuration

n8n is pre-configured with:

- ARK API URL accessible in-cluster
- Persistent storage for workflows
- HTTPRoute for external access via localhost-gateway

## Notes

- Requires Kubernetes cluster with ARK installed
- Data persists in a 1Gi PVC
- Accessible via localhost-gateway on port 8080
