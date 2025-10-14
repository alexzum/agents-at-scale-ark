# Simple Agent

A complete A2A server example with conversation, math, and echo capabilities.

## Quick Start

```bash
# Local development
make init
make dev

# Kubernetes deployment
make install
```

## Test It

```bash
# Health check
curl http://localhost:8000/health

# Agent discovery
curl http://localhost:8000/.well-known/agent.json | jq .

# Send a message
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "execute",
    "params": {
      "message": {
        "parts": [{"text": "Hello! How are you?"}]
      }
    },
    "id": 1
  }' | jq .
```

## ARK Integration

```bash
# Query through ARK
fark agent simple-agent-simple-agent "Hello, what can you do?"
```

## Available Commands

- `make dev` - Run locally
- `make install` - Deploy to Kubernetes
- `make status` - Check deployment
- `make logs` - View logs
- `make test-local` - Test endpoints
