# Go Task Agent

Go A2A Agent that returns task structures for debugging protocol issues.

## Quickstart

```bash
# Show all available recipes
make help

# Build and run locally
make run

# Build Docker image  
make docker-build

# Run in Docker
make docker-run
```

## Development

The agent runs on port 8082 and provides:
- `/.well-known/agent.json` - Agent discovery
- `/.well-known/agent-card.json` - Modern agent discovery  
- `/` - Main JSONRPC endpoint (returns task structures)
- `/health` - Health check

This agent demonstrates the task structure format issue by returning `{"kind": "task"}` directly instead of wrapping in message structures.