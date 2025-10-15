# Simple Agent

A complete A2A server example with conversation, math, and echo capabilities.

## Quick Start

### Option 1: Integrated with ARK (Recommended)
```bash
# Start ARK with simple-agent automatically connected
devspace dev
```

### Option 2: Manual Setup
```bash
# Install dependencies and start the server
make init
make dev

# Then register with ARK manually
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
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "test-1",
        "contextId": "ctx-1",
        "role": "user",
        "parts": [{"kind": "text", "text": "Hello! How are you?"}]
      }
    },
    "id": 1
  }' | jq .
```

## ARK Integration

Once your A2A server is running, integrate it with ARK:

```bash
# Create A2AServer resource
kubectl apply -f - <<EOF
apiVersion: ark.mckinsey.com/v1prealpha1
kind: A2AServer
metadata:
  name: simple-agent
spec:
  address:
    value: "http://host.docker.internal:8000"
  description: "Simple agent with conversation, math, and echo capabilities"
EOF

# Query through ARK
fark agent simple-agent-simple-agent "Hello, what can you do?"
```

## Available Commands

- `make dev` - Run locally
- `make install` - Show integration instructions
- `make status` - Check ARK integration
- `make logs` - View logs
- `make test-local` - Test endpoints