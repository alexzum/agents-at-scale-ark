# MCP Filesystem Server with Session Management

MCP Filesystem Server with persistent session support, LRU eviction, and reconnection capabilities.

## Quickstart

```bash
# Show all available recipes.
make help

# Install/uninstall - sets up your local machine or cluster.
make install
make uninstall

# Run in development mode. May require extra tools and setup, check the README.
make dev
```

## Features

- **Persistent Sessions**: Sessions survive server restarts via file-based storage
- **LRU Eviction**: Automatically evicts least recently used sessions when limit reached
- **Reconnection**: Clients can reconnect with same session ID and maintain configuration
- **Session Isolation**: Each session operates in isolated directory (`/data/{sessionId}/`)
- **All Filesystem Operations**: Read, write, edit, move, search, list, tree

Based on the marketplace filesystem MCP adapter with enhanced session management.

## Testing

See `LOCAL_TESTING.md` for comprehensive test procedures covering:
- Session ID generation and persistence
- Reconnection across pod restarts
- LRU eviction (basic and access-based)
- Session isolation and explicit deletion

## Configuration

Environment variables (configured in `chart/values.yaml`):
- `PORT`: Server port (default: 8080)
- `SESSION_FILE`: Path to session storage file (default: /data/sessions/sessions.json)
- `MAX_SESSIONS`: Maximum concurrent sessions (default: 1000)
- `CLEANUP_SESSION_FILES`: Delete session directories on eviction (default: false)

Helm chart options:
- `persistence.size`: Storage size for `/data` volume (default: 10Gi)
- `persistence.storageClass`: Storage class for PVC
- `resources`: CPU and memory limits/requests

## Using with ARK

The MCP server creates an `MCPServer` resource that auto-generates tools with the `mcp-filesystem-` prefix.

Example agent configuration:

```yaml
apiVersion: ark.mckinsey.com/v1alpha1
kind: Agent
metadata:
  name: filesystem
spec:
  tools:
    - name: mcp-filesystem-read-file
      type: custom
    - name: mcp-filesystem-write-file
      type: custom
    - name: mcp-filesystem-edit-file
      type: custom
    - name: mcp-filesystem-create-directory
      type: custom
    - name: mcp-filesystem-list-directory
      type: custom
```

See `samples/agents/filesystem.yaml` for complete configuration.

Example query:

```bash
ark query agent/filesystem "Create a file hello.txt with content 'Hello World', then list all files"
```

For detailed usage examples and session management, see `docs/content/user-guide/samples/mcp-servers.mdx`.

## Architecture

Wrapper + adapter pattern:
- **Wrapper** (`src/index.ts`): Session management, persistence, LRU eviction
- **Adapter** (`src/filesystem/`): MCP protocol, file operations, path validation

Each session gets isolated `FilesystemContext` with its own base directory and allowed directories.