# Simple A2A Server

A minimal working example of an A2A (Agent-to-Agent) server that demonstrates basic functionality and integration with ARK.

## Overview

This sample demonstrates how to create a simple A2A-compatible agent that can:
- Engage in basic conversation
- Perform simple mathematical calculations
- Echo back user messages
- Provide information about itself

The server implements the [A2A Protocol](https://github.com/a2a-integration/a2a-spec) and integrates seamlessly with ARK's agent ecosystem.

## Features

- **Basic Conversation**: Responds to greetings and general conversation
- **Simple Math**: Performs basic arithmetic operations (addition, multiplication)
- **Echo Functionality**: Repeats back user messages
- **Self-Description**: Provides information about its capabilities
- **A2A Protocol Compliance**: Full implementation of A2A specification
- **Health Monitoring**: Built-in health check endpoints
- **Container Ready**: Dockerized for easy deployment

## Quick Start

### Prerequisites

- Python 3.8+
- Docker (for containerized deployment)
- Kubernetes cluster with ARK installed
- Helm 3.x

### Local Development

1. **Clone and navigate to the sample:**
   ```bash
   cd samples/a2a/simple-a2a-server
   ```

2. **Install dependencies:**
   ```bash
   make init
   ```

3. **Run in development mode:**
   ```bash
   make dev
   ```

4. **Test the server:**
   ```bash
   # In another terminal
   make test-local
   ```

The server will be available at:
- `http://localhost:8000/.well-known/agent.json` - Agent discovery
- `http://localhost:8000/health` - Health check
- `http://localhost:8000/` - A2A JSON-RPC endpoint

### Kubernetes Deployment

1. **Deploy to your cluster:**
   ```bash
   make install
   ```

2. **Check status:**
   ```bash
   make status
   ```

3. **View logs:**
   ```bash
   make logs
   ```

4. **Port forward for local testing:**
   ```bash
   make port-forward
   ```

## Usage Examples

### Agent Discovery

```bash
# Get agent card
curl http://localhost:8000/.well-known/agent.json | jq .
```

### Basic Conversation

```bash
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
  }'
```

### Math Operations

```bash
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "execute",
    "params": {
      "message": {
        "parts": [{"text": "Calculate 5 + 3"}]
      }
    },
    "id": 1
  }'
```

### Echo Messages

```bash
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "execute",
    "params": {
      "message": {
        "parts": [{"text": "Echo: This is a test message"}]
      }
    },
    "id": 1
  }'
```

## ARK Integration

Once deployed, the A2AServer automatically creates an agent resource in ARK:

```bash
# List discovered agents
kubectl get agents

# Query the agent through ARK
fark agent simple-a2a-server-simple-a2a-agent "Hello, what can you do?"
```

### Query Examples

```yaml
apiVersion: ark.mckinsey.com/v1alpha1
kind: Query
metadata:
  name: greeting-test
spec:
  input: "Hello! How are you today?"
  targets:
    - type: agent
      name: simple-a2a-server-simple-a2a-agent
```

## Architecture

### Components

1. **SimpleAgentExecutor**: Core agent logic that processes messages
2. **Agent Card**: Describes capabilities and skills
3. **A2A Application**: Handles protocol compliance
4. **Health Endpoints**: Monitoring and status checks

### Request Flow

1. Client sends JSON-RPC request to `/`
2. A2A application validates and routes request
3. SimpleAgentExecutor processes the message
4. Response sent back through event queue
5. Client receives structured response

### Skills

The agent exposes three main skills:

1. **Basic Conversation** (`basic_conversation`)
   - Responds to greetings
   - Provides general conversation

2. **Simple Math** (`simple_math`)
   - Performs arithmetic operations
   - Handles addition and multiplication

3. **Echo Messages** (`echo_messages`)
   - Repeats user input
   - Useful for testing

## Development

### Project Structure

```
simple-a2a-server/
├── src/simple_a2a_server/     # Source code
│   ├── __init__.py
│   ├── __main__.py
│   └── main.py               # Main server implementation
├── chart/                     # Helm chart
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
├── Dockerfile                 # Container definition
├── Makefile                   # Build and deployment commands
├── pyproject.toml            # Python dependencies
└── README.md                  # This file
```

### Available Make Targets

- `make help` - Show all available commands
- `make init` - Install dependencies
- `make dev` - Run in development mode
- `make lint` - Run linting and type checking
- `make build` - Build Docker image
- `make install` - Deploy to Kubernetes
- `make uninstall` - Remove from Kubernetes
- `make status` - Show deployment status
- `make logs` - View application logs
- `make port-forward` - Port forward for local access
- `make test-local` - Test local endpoints

### Linting

```bash
# Check code quality
make lint

# Fix formatting issues
make lint-fix
```

## Configuration

### Environment Variables

- `A2A_HOST` - Server host (default: `0.0.0.0`)
- `A2A_PORT` - Server port (default: `8000`)
- `A2A_SERVER_URL` - Public URL for agent card (default: `http://localhost:8000`)

### Helm Values

Key configuration options in `chart/values.yaml`:

```yaml
# Replica count
replicaCount: 1

# Resource limits
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi

# A2AServer configuration
a2aserver:
  enabled: true
  description: "Simple A2A Server demonstrating basic functionality"
```

## Troubleshooting

### Common Issues

**Agent not discovered:**
```bash
# Check A2AServer status
kubectl describe a2aserver simple-a2a-server

# Verify agent card
curl http://localhost:8000/.well-known/agent.json
```

**Connection refused:**
```bash
# Check pod status
kubectl get pods -l app=simple-a2a-server

# Check logs
make logs
```

**Query execution fails:**
```bash
# Test with A2A Inspector
# Visit: https://inspector.a2a-integration.org
# Enter: http://localhost:8000
```

### Debug Mode

Enable debug logging:

```bash
# Set environment variable
export A2A_LOG_LEVEL=debug

# Run in debug mode
make dev
```

## Extending the Agent

### Adding New Skills

1. **Define the skill** in `create_agent_card()`:
   ```python
   AgentSkill(
       id="new_skill",
       name="New Skill",
       description="What this skill does",
       tags=["tag1", "tag2"],
       examples=["example input"],
       inputModes=["text/plain"],
       outputModes=["text/plain"],
   )
   ```

2. **Implement the logic** in `_process_message()`:
   ```python
   elif "new_skill" in message_lower:
       return "Response for new skill"
   ```

3. **Update tests** to cover the new functionality

### Adding External Dependencies

1. **Update `pyproject.toml`** with new dependencies
2. **Update `Dockerfile`** if system packages are needed
3. **Update Helm values** for any configuration changes

## Production Considerations

### Security

- Runs as non-root user (UID 1001)
- Read-only root filesystem
- Minimal attack surface
- No unnecessary dependencies

### Monitoring

- Health check endpoint at `/health`
- Structured logging
- Resource limits configured
- Liveness and readiness probes

### Scaling

- Stateless design allows horizontal scaling
- Configure `autoscaling` in Helm values
- Monitor resource usage and adjust limits

## Next Steps

- **Framework Integration**: Extend with LangChain, CrewAI, or AutoGen
- **Advanced Skills**: Add more sophisticated capabilities
- **Streaming**: Implement streaming responses
- **Authentication**: Add security layers
- **Metrics**: Integrate with monitoring systems

## Related Documentation

- [A2A Servers](/developer-guide/a2a-server) - ARK A2A server documentation
- [Building A2A Servers](/developer-guide/building-a2a-servers) - Complete development guide
- [A2A Gateway](/developer-guide/a2a-gateway) - ARK's A2A gateway
- [A2A Protocol Spec](https://github.com/a2a-integration/a2a-spec) - Official protocol documentation

## Contributing

This sample is part of the ARK project. See [CONTRIBUTING.md](../../../CONTRIBUTING.md) for guidelines on contributing to ARK samples.
