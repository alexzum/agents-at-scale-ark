# A2A Samples

This directory contains complete, runnable examples of A2A (Agent-to-Agent) servers that demonstrate different levels of complexity and functionality.

## Available Samples

### 🚀 **Getting Started**

#### [Basic A2A Server](basic-a2a-server/)
**The absolute minimum A2A server - just 80 lines of code!**

- ✅ Minimal implementation
- ✅ Echo functionality
- ✅ Health check and agent discovery
- ✅ Perfect for learning the A2A protocol

```bash
cd basic-a2a-server
pip install -r requirements.txt
python minimal_server.py
```

### 🏗️ **Production Ready**

#### [Simple A2A Server](simple-a2a-server/)
**Full-featured A2A server with multiple capabilities**

- ✅ Basic conversation
- ✅ Simple math operations
- ✅ Echo functionality
- ✅ Docker containerization
- ✅ Helm chart for Kubernetes
- ✅ Comprehensive error handling
- ✅ Production deployment ready

```bash
cd simple-a2a-server
make init
make dev
```

### 🔧 **Framework Integration**

#### [Hosted LangChain Agents](../agent-hosting/hosted-langchain-agents/)
**LangChain weather agent with real API integrations**

- ✅ LangChain framework integration
- ✅ Weather forecasting with NWS API
- ✅ Real-world tool usage
- ✅ Production deployment

```bash
cd ../agent-hosting/hosted-langchain-agents
make install
```

## Quick Comparison

| Sample | Lines of Code | Features | Use Case |
|--------|---------------|----------|----------|
| **Basic A2A Server** | ~80 | Echo only | Learning, minimal setup |
| **Simple A2A Server** | ~400 | Conversation, Math, Echo | Production, full features |
| **LangChain Agents** | ~500+ | Weather API, LangChain | Framework integration |

## How to Choose

- **Learning A2A Protocol**: Start with [Basic A2A Server](basic-a2a-server/)
- **Building Production Apps**: Use [Simple A2A Server](simple-a2a-server/)
- **Integrating Existing Frameworks**: See [Hosted LangChain Agents](../agent-hosting/hosted-langchain-agents/)

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
