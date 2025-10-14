# Minimal A2A Server

The absolute minimum A2A server implementation - just 80 lines of code!

## What it does

- Echoes back any message you send to it
- Implements the A2A protocol correctly
- Has health check and agent discovery endpoints

## How to run

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python minimal_server.py
```

## Test it

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
        "parts": [{"kind": "text", "text": "Hello world"}]
      }
    },
    "id": 1
  }' | jq .
```

That's it! This is the absolute minimum you need for a working A2A server.
