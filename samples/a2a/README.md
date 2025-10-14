# A2A Samples

This directory contains complete, runnable examples of A2A (Agent-to-Agent) servers that demonstrate different levels of complexity and functionality.

## Available Samples

### 🚀 **Getting Started**

#### [Simple Agent](simple-agent/)
**Complete A2A server example with production-ready features**

- ✅ Basic conversation
- ✅ Simple math operations
- ✅ Echo functionality
- ✅ Docker containerization
- ✅ Helm chart for Kubernetes
- ✅ Comprehensive error handling
- ✅ Production deployment ready
- ✅ Perfect for learning the A2A protocol

```bash
cd simple-agent
make init
make dev
```

### 🔧 **Framework Integration**

#### [Weather Agent](weather-agent/)
**Weather agent with real API integrations**

- ✅ Weather forecasting capabilities
- ✅ Real-world API usage
- ✅ Production deployment ready

```bash
cd weather-agent
make install
```

## Quick Comparison

| Sample | Lines of Code | Features | Use Case |
|--------|---------------|----------|----------|
| **Simple Agent** | ~400 | Conversation, Math, Echo | Learning, production |
| **Weather Agent** | ~500+ | Weather API, LangChain | Framework integration |

## How to Choose

- **Learning A2A Protocol**: Start with [Simple Agent](simple-agent/)
- **Building Production Apps**: Use [Simple Agent](simple-agent/)
- **Integrating Existing Frameworks**: See [Weather Agent](weather-agent/)

## Testing Your A2A Server

All samples can be tested using:

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

## Integration with ARK

Once your A2A server is running, you can integrate it with ARK by creating an A2AServer resource:

```yaml
apiVersion: ark.mckinsey.com/v1prealpha1
kind: A2AServer
metadata:
  name: my-a2a-server
spec:
  address:
    value: "http://localhost:8000"
  description: "My A2A server"
```

ARK will automatically discover your agent and make it available for queries!

## Next Steps

- [Building A2A Servers](../../docs/content/developer-guide/building-a2a-servers) - Complete development guide
- [A2A Servers](../../docs/content/developer-guide/a2a-server) - ARK A2A server documentation
- [A2A Gateway](../../docs/content/developer-guide/a2a-gateway) - ARK's A2A gateway
