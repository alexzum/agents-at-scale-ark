# MCP Filesystem Server with Session Management

MCP Filesystem Server with persistent session support, LRU eviction, and reconnection capabilities.

## Features

- **Persistent Sessions**: Sessions survive server restarts via file-based storage
- **LRU Eviction**: Automatically evicts least recently used sessions when limit reached
- **Reconnection**: Clients can reconnect with same session ID and maintain configuration
- **Configurable**: Environment variables for port, session file path, and max sessions
- **All Filesystem Operations**: Read, write, search, list, tree, edit files and directories

Based on the marketplace filesystem MCP adapter with enhanced session management.

## Local Testing (Quick Start)

```bash
# From the mcp/filesystem-mcp directory
cd mcp/filesystem-mcp

# Build and deploy to your local cluster
make build
make install

# Verify deployment
kubectl get pods -l app.kubernetes.io/name=mcp-filesystem
kubectl get mcpserver mcp-filesystem

# Port forward to test locally
kubectl port-forward svc/mcp-filesystem-server 8080:8080

# Test health endpoint
curl http://localhost:8080/health

# Initialize session with custom path
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "method":"initialize",
    "params":{
      "protocolVersion":"0.1.0",
      "capabilities":{},
      "meta":{"path":"user-uploads"}
    },
    "id":1
  }'
# Save the Mcp-Session-Id from response headers

# Reconnect with session ID
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: <your-session-id>" \
  -d '{
    "jsonrpc":"2.0",
    "method":"tools/list",
    "params":{},
    "id":2
  }'

# Uninstall
make uninstall
```

## Prerequisites

- Kubernetes cluster (kind, minikube, or other)
- Helm 3.x
- kubectl configured to access your cluster
- Docker (for building images)
- **ARK controller deployed** - Run `make quickstart` from project root to install ARK with MCPServer CRD

## Build and Deploy

### 1. Build Docker Image

```bash
# Install dependencies and build TypeScript
npm install
npm run build

# Build Docker image
docker build -t filesystem-mcp-server:latest .

# Load into local cluster
# kind load docker-image filesystem-mcp-server:latest
# OR for minikube:
minikube image load filesystem-mcp-server:latest
```

### 2. Deploy with Helm

```bash
# Install
helm install mcp-filesystem ./chart

# Upgrade if already installed
helm upgrade mcp-filesystem ./chart

# With custom values
helm install mcp-filesystem ./chart -f custom-values.yaml
```

### 3. Verify Deployment

```bash
# Check all resources
kubectl get pods -l app.kubernetes.io/name=mcp-filesystem
kubectl get svc mcp-filesystem-server
kubectl get mcpserver mcp-filesystem
kubectl get pvc
```

## Configuration

Environment variables (configured in `values.yaml`):
- `PORT`: Server port (default: 8080)
- `SESSION_FILE`: Path to session storage file (default: /data/sessions/sessions.json)
- `MAX_SESSIONS`: Maximum number of active sessions (default: 1000)
- `CLEANUP_SESSION_FILES`: Delete session directories on deletion/eviction (default: false)

Key Helm configuration options:
- `persistence.size`: Storage size for the `/data` volume (default: 10Gi)
- `persistence.storageClass`: Storage class for PVC
- `resources`: CPU and memory limits/requests

## Using with ARK Agents

The MCP server exposes tools with the `mcp-filesystem-` prefix. See `samples/agents/filesystem.yaml` for example agent configuration.

Available tools:
- `mcp-filesystem-read-file`, `mcp-filesystem-write-file`, `mcp-filesystem-modify-file`
- `mcp-filesystem-create-directory`, `mcp-filesystem-list-directory`, `mcp-filesystem-tree`
- `mcp-filesystem-search-files`, `mcp-filesystem-search-within-files`
- And more - see filesystem adapter for full list

## Implementation Details

This implementation enhances the marketplace filesystem MCP server (`agents-at-scale-marketplace/mcp-servers/filesystem`) with:
- File-based session persistence to `/data/sessions/sessions.json`
- LRU eviction when `MAX_SESSIONS` limit reached
- Reconnection support: transport closes don't lose session data
- All filesystem operations from marketplace adapter unchanged