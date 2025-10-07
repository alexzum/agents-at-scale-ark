# ARK + n8n Integration Specification

**Version:** 1.0
**Date:** 2024-01-01
**Status:** Implementation Complete (Phase 1 MVP)

## Executive Summary

This specification defines the integration between n8n (workflow automation platform) and ARK (Agentic Runtime for Kubernetes), enabling users to build low-code agentic workflows through n8n's visual interface while leveraging ARK's agent execution capabilities.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [API Design](#api-design)
5. [Deployment](#deployment)
6. [Workflows](#workflows)
7. [Future Enhancements](#future-enhancements)
8. [Testing Strategy](#testing-strategy)
9. [Security Considerations](#security-considerations)
10. [Success Metrics](#success-metrics)

## 1. Overview

### 1.1 Goals

- Enable visual workflow creation for ARK agents via n8n
- Provide simplified API for agent execution
- Support both in-cluster and external n8n deployments
- Maintain ARK's existing query-based architecture
- Provide path to custom n8n community nodes (future)

### 1.2 Non-Goals (Phase 1)

- Custom n8n community node package
- Webhook-based query completion callbacks
- Streaming response support in n8n
- Authentication/authorization (using AUTH_MODE=open)

### 1.3 Use Cases

**Primary:**
- Execute ARK agent queries from n8n workflows
- Build multi-step agentic workflows visually
- Integrate ARK agents with external services via n8n

**Secondary:**
- Prototype agent interactions quickly
- Schedule periodic agent queries
- Create webhook-triggered agent endpoints
- Chain multiple agents in sequence or parallel

## 2. Architecture

### 2.1 System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
│                                                               │
│  ┌──────────┐         ┌──────────┐         ┌──────────┐    │
│  │   n8n    │────────▶│ ARK API  │────────▶│  Agent   │    │
│  │  (Pod)   │  HTTP   │  (Pod)   │   K8s   │  (CRD)   │    │
│  └──────────┘         └──────────┘         └──────────┘    │
│       │                     │                     │          │
│       │                     │                     │          │
│  ┌────▼────┐           ┌───▼────┐          ┌────▼─────┐   │
│  │   PVC   │           │ Query  │          │ Executor │   │
│  │ (Data)  │           │ (CRD)  │          │  Engine  │   │
│  └─────────┘           └────────┘          └──────────┘   │
│                                                               │
└───────────────────────────┬───────────────────────────────┘
                            │
                            │ HTTPRoute
                            ▼
                   ┌──────────────────┐
                   │ localhost-gateway │
                   │    (port 8080)    │
                   └──────────────────┘
                            │
                            ▼
                    External Access
```

### 2.2 Component Interactions

1. **n8n → ARK API**: HTTP requests for listing agents and executing queries
2. **ARK API → K8s**: Creates/manages Query CRs via ark-sdk
3. **Query CR → Executor**: Kubernetes controller dispatches query to execution engine
4. **Executor → Agent**: Executes agent logic with configured model
5. **ARK API ← K8s**: Polls Query CR status until completion
6. **n8n ← ARK API**: Returns formatted response

### 2.3 Data Flow

**Synchronous Execution (wait=true):**
```
User (n8n) → POST /v1/agents/{name}/execute
           → ARK API creates Query CR
           → ARK API polls Query status (1s interval)
           → Query completes
           → ARK API extracts response
           ← Returns formatted result
```

**Asynchronous Execution (wait=false):**
```
User (n8n) → POST /v1/agents/{name}/execute
           → ARK API creates Query CR
           ← Returns queryName immediately
User (n8n) → GET /v1/queries/{queryName} (polling)
           ← Returns query status and response
```

## 3. Components

### 3.1 n8n Service

**Location:** `services/n8n/`

**Purpose:** Deploy n8n workflow automation platform to Kubernetes

**Components:**
- `chart/` - Helm chart for Kubernetes deployment
  - `Chart.yaml` - Helm chart metadata
  - `values.yaml` - Default configuration values
  - `templates/deployment.yaml` - n8n Deployment
  - `templates/service.yaml` - ClusterIP Service
  - `templates/pvc.yaml` - PersistentVolumeClaim for data
  - `templates/httproute.yaml` - Gateway API route
- `build.mk` - Makefile integration
- `devspace.yaml` - DevSpace configuration
- `README.md` - Service documentation
- `CLAUDE.md` - Development guidelines
- `manifest.yaml` - Service metadata

**Configuration:**
```yaml
app:
  image:
    repository: docker.n8n.io/n8nio/n8n
    tag: latest
  env:
    N8N_HOST: n8n.default.127.0.0.1.nip.io
    ARK_API_URL: http://ark-api.default.svc.cluster.local:8000

storage:
  enabled: true
  size: 1Gi

httpRoute:
  enabled: true
  hostnames:
    - n8n.default.127.0.0.1.nip.io
```

### 3.2 ARK API Execute Endpoint

**Location:** `services/ark-api/ark-api/src/ark_api/api/v1/agents.py`

**Purpose:** Simplified agent execution API for external integrations

**Endpoint:** `POST /v1/agents/{agent_name}/execute`

**Request Model:**
```python
class AgentExecuteRequest(BaseModel):
    input: str                          # Required: query text
    wait: bool = True                   # Wait for completion
    timeout: Optional[str] = "300s"     # Max wait time
    sessionId: Optional[str] = None     # Session for context
    memory: Optional[str] = None        # Memory resource
    parameters: Optional[List[Parameter]] = None  # Custom params
```

**Response Model:**
```python
class AgentExecuteResponse(BaseModel):
    queryName: str              # Generated query CR name
    input: str                  # Original input
    response: Optional[str]     # Agent response (if completed)
    status: str                 # "pending", "completed", "failed", "timeout"
    duration: Optional[str]     # Execution time
    error: Optional[str]        # Error message (if failed)
```

**Implementation Details:**
- Auto-generates unique query name: `{agent_name}-{uuid}`
- Creates Query CR with specified parameters
- If `wait=true`: Polls Query status every 1 second
- Extracts response from Query CR status
- Returns formatted result
- Handles timeouts, failures, and errors

### 3.3 Workflow Templates

**Location:** `services/n8n/n8n-workflows/`

**Files:**
- `README.md` - Template documentation
- `ark-agent-query-basic.json` - Basic manual trigger workflow
- `ark-agent-query-with-params.json` - Webhook-triggered workflow

**Basic Workflow Structure:**
```
Manual Trigger
  → HTTP Request: List Agents
    → Code: Extract Agent Names
      → HTTP Request: Execute Agent
        → Code: Format Response
```

**Webhook Workflow Structure:**
```
Webhook Trigger
  → Code: Parse Input Parameters
    → HTTP Request: Execute Agent
      → IF: Check Status
        → Format Success Response → Respond to Webhook
        → Format Error Response → Respond to Webhook
```

## 4. API Design

### 4.1 Execute Endpoint Specification

**Method:** POST
**Path:** `/v1/agents/{agent_name}/execute`
**Content-Type:** `application/json`

**Path Parameters:**
- `agent_name` (string, required): Name of agent to execute

**Query Parameters:**
- `namespace` (string, optional): Kubernetes namespace (defaults to current context)

**Request Body:**
```json
{
  "input": "What is the capital of France?",
  "wait": true,
  "timeout": "60s",
  "sessionId": "user-123-session",
  "memory": "conversation-memory",
  "parameters": [
    {
      "name": "temperature",
      "value": "0.7"
    }
  ]
}
```

**Response (Success):**
```json
{
  "queryName": "my-agent-a1b2c3d4",
  "input": "What is the capital of France?",
  "response": "The capital of France is Paris.",
  "status": "completed",
  "duration": "1.8s"
}
```

**Response (Failure):**
```json
{
  "queryName": "my-agent-a1b2c3d4",
  "input": "What is the capital of France?",
  "status": "failed",
  "duration": "0.5s",
  "error": "Agent not available"
}
```

**Response (Timeout):**
```json
{
  "queryName": "my-agent-a1b2c3d4",
  "input": "What is the capital of France?",
  "status": "timeout",
  "duration": "60s",
  "error": "Query did not complete within 60 seconds"
}
```

**Response (Async - wait=false):**
```json
{
  "queryName": "my-agent-a1b2c3d4",
  "input": "What is the capital of France?",
  "status": "pending",
  "duration": null,
  "response": null
}
```

**HTTP Status Codes:**
- `200 OK` - Query executed successfully (check response.status for completion)
- `404 Not Found` - Agent not found
- `422 Unprocessable Entity` - Invalid request parameters
- `500 Internal Server Error` - Server error

### 4.2 Error Handling

**Agent Not Found:**
```json
{
  "detail": "Agent 'non-existent-agent' not found"
}
```

**Timeout Parsing Error:**
```json
{
  "detail": "Invalid timeout format. Use format like '60s' or '5m'"
}
```

**Query Creation Failed:**
```json
{
  "detail": "Kubernetes API error: Forbidden"
}
```

### 4.3 Existing Endpoints Used

**List Agents:**
```
GET /v1/agents?namespace=default

Response:
{
  "items": [
    {
      "name": "my-agent",
      "namespace": "default",
      "description": "A helpful agent",
      "available": "available"
    }
  ],
  "count": 1
}
```

**Get Query Status (for async):**
```
GET /v1/queries/{query_name}?namespace=default

Response:
{
  "name": "my-agent-a1b2c3d4",
  "namespace": "default",
  "input": "What is the capital of France?",
  "status": {
    "state": "completed",
    "responses": [
      {
        "target": {"type": "agent", "name": "my-agent"},
        "content": "The capital of France is Paris."
      }
    ]
  }
}
```

## 5. Deployment

### 5.1 Prerequisites

- Kubernetes cluster with ARK installed
- localhost-gateway deployed
- ARK API running

### 5.2 Installation Steps

```bash
# Install n8n to cluster
make n8n-install

# Verify installation
kubectl get pods -n default -l app=n8n

# Check routes
make routes

# Access n8n UI
# Open http://n8n.default.127.0.0.1.nip.io:8080
```

### 5.3 Uninstallation

```bash
make n8n-uninstall
```

### 5.4 Development Mode

```bash
# Port-forward to n8n for local access
make n8n-dev

# Access at http://localhost:5678
```

### 5.5 Resource Requirements

**n8n Pod:**
- CPU: 250m (request), 500m (limit)
- Memory: 256Mi (request), 512Mi (limit)
- Storage: 1Gi PVC

**ARK API:**
- No additional resources required
- Execute endpoint uses existing query infrastructure

### 5.6 Configuration Options

**In-Cluster ARK API URL:**
```
http://ark-api.default.svc.cluster.local
```

**External ARK API URL (via gateway):**
```
http://ark-api.default.127.0.0.1.nip.io:8080
```

**Custom Namespace:**
```bash
make n8n-install N8N_NAMESPACE=my-namespace
```

## 6. Workflows

### 6.1 Basic Agent Query

**File:** `services/n8n/n8n-workflows/ark-agent-query-basic.json`

**Nodes:**
1. **Manual Trigger** - Start workflow manually
2. **HTTP Request (List Agents)** - GET /v1/agents
3. **Code (Extract Names)** - Parse agent list, select first agent
4. **HTTP Request (Execute)** - POST /v1/agents/{name}/execute
5. **Code (Format Response)** - Structure output

**Use Case:** Test agent execution, explore available agents

### 6.2 Webhook-Triggered Query

**File:** `services/n8n/n8n-workflows/ark-agent-query-with-params.json`

**Nodes:**
1. **Webhook Trigger** - Receive HTTP POST
2. **Code (Parse Input)** - Extract agent name, input, params
3. **HTTP Request (Execute)** - POST /v1/agents/{name}/execute
4. **IF (Check Status)** - Branch on success/failure
5. **Code (Format Success)** - Structure success response
6. **Code (Format Error)** - Structure error response
7. **Respond to Webhook** - Return HTTP response

**Use Case:** External API integration, chatbot backend, scheduled queries

**Example Call:**
```bash
curl -X POST http://n8n.default.127.0.0.1.nip.io:8080/webhook/ark-agent-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "my-agent",
    "input": "What can you do?",
    "timeout": "30s"
  }'
```

### 6.3 Common Patterns

**Sequential Chaining:**
```
Execute Agent 1
  → Extract response
    → Execute Agent 2 with Agent 1 output
      → Combine results
```

**Parallel Execution:**
```
Manual Trigger
  → Split In Batches
    → Execute Agent (parallel)
      → Merge responses
```

**Error Handling:**
```
Execute Agent
  → IF status === "completed"
    → Success path
  → ELSE
    → Retry with exponential backoff
    → Send error notification
```

## 7. Future Enhancements

### 7.1 Phase 2: Custom n8n Community Node

**Package:** `n8n-nodes-ark`

**Features:**
- Native ARK node types in n8n palette
- Dynamic dropdowns for agents/models/teams
- Type-safe parameter inputs
- Built-in credential management
- Streaming response support

**Nodes:**
- ARK Agent Query
- ARK Model Query
- ARK Team Query
- ARK Evaluation Trigger

**Implementation:**
```typescript
class ArkAgentNode implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'ARK Agent',
    name: 'arkAgent',
    group: ['transform'],
    properties: [
      {
        displayName: 'Agent',
        name: 'agent',
        type: 'options',
        typeOptions: {
          loadOptionsMethod: 'getAgents'
        }
      },
      {
        displayName: 'Input',
        name: 'input',
        type: 'string'
      }
    ]
  };
}
```

### 7.2 Phase 3: Webhook Callbacks

**Feature:** ARK calls n8n webhook when query completes

**API Enhancement:**
```json
POST /v1/agents/my-agent/execute
{
  "input": "Hello",
  "wait": false,
  "webhookUrl": "http://n8n.default.svc.cluster.local:5678/webhook/ark-callback"
}
```

**ARK Implementation:**
- Store webhook URL in Query CR annotation
- Executor sends POST to webhook on completion
- n8n Webhook Trigger receives callback

### 7.3 Phase 4: Streaming Support

**Feature:** Real-time streaming of agent responses

**Implementation:**
- n8n opens SSE connection to ARK API
- ARK proxies to memory service streaming endpoint
- Chunks streamed back to n8n in real-time

### 7.4 Phase 5: Authentication

**Feature:** OIDC/JWT authentication for production

**Configuration:**
```yaml
# n8n credentials
type: ark-api-auth
fields:
  - name: baseUrl
  - name: token
```

**ARK API:**
```bash
AUTH_MODE=sso
OIDC_ISSUER_URL=https://auth.example.com
```

## 8. Testing Strategy

### 8.1 Unit Tests

**ARK API Execute Endpoint:**
```python
# Test file: tests/api/test_agents_execute.py

async def test_execute_agent_wait_true():
    response = await client.post(
        "/v1/agents/test-agent/execute",
        json={"input": "Hello", "wait": True}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

async def test_execute_agent_not_found():
    response = await client.post(
        "/v1/agents/non-existent/execute",
        json={"input": "Hello"}
    )
    assert response.status_code == 404
```

### 8.2 Integration Tests

**n8n Workflow Execution:**
```bash
# Deploy n8n and ARK
make quickstart
make n8n-install

# Import workflow
# Execute manually
# Verify results
```

### 8.3 End-to-End Tests

**Complete Flow:**
1. Create test agent
2. Import n8n workflow
3. Execute workflow
4. Verify query created
5. Verify response returned
6. Clean up resources

### 8.4 Performance Tests

**Load Testing:**
```bash
# Execute 100 concurrent queries via n8n
# Measure response times
# Verify no query failures
# Check resource usage
```

## 9. Security Considerations

### 9.1 Current State (Phase 1 MVP)

- **Authentication:** Disabled (AUTH_MODE=open)
- **Authorization:** None
- **Network:** In-cluster communication only
- **Data:** Workflows stored in n8n PVC

### 9.2 Production Recommendations

**Authentication:**
- Enable AUTH_MODE=sso
- Configure OIDC_ISSUER_URL
- Generate JWT tokens for n8n
- Store tokens in n8n credentials

**Network Security:**
- Use NetworkPolicies to restrict traffic
- Enable TLS for ARK API
- Use ingress with TLS termination

**Data Security:**
- Encrypt PVC at rest
- Use Secrets for sensitive parameters
- Enable audit logging
- Implement RBAC for Query CRs

**Example NetworkPolicy:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: n8n-to-ark-api
spec:
  podSelector:
    matchLabels:
      app: n8n
  policyTypes:
    - Egress
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: ark-api
      ports:
        - protocol: TCP
          port: 8000
```

## 10. Success Metrics

### 10.1 Phase 1 MVP Criteria

- [x] n8n deployed to cluster
- [x] Accessible via localhost-gateway
- [x] Execute endpoint functional
- [x] Sample workflows work end-to-end
- [x] Documentation complete
- [ ] Integration tests passing (pending implementation)

### 10.2 Performance Targets

- Agent execution latency: < 5s (excluding model inference time)
- n8n UI response time: < 100ms
- Concurrent workflows: > 10
- Query throughput: > 100/minute

### 10.3 User Adoption Metrics

- Number of n8n workflows created
- Unique agents queried via n8n
- Average workflow complexity (nodes per workflow)
- User satisfaction score

## 11. Appendices

### 11.1 File Structure

```
ark-oss/
├── services/
│   ├── n8n/
│   │   ├── chart/
│   │   │   ├── Chart.yaml
│   │   │   ├── values.yaml
│   │   │   └── templates/
│   │   │       ├── deployment.yaml
│   │   │       ├── service.yaml
│   │   │       ├── pvc.yaml
│   │   │       └── httproute.yaml
│   │   ├── build.mk
│   │   ├── devspace.yaml
│   │   ├── manifest.yaml
│   │   ├── README.md
│   │   └── CLAUDE.md
│   └── ark-api/
│       └── ark-api/
│           └── src/
│               └── ark_api/
│                   ├── api/
│                   │   └── v1/
│                   │       └── agents.py (execute endpoint)
│                   └── models/
│                       └── agents.py (execute models)
├── samples/
│   └── n8n-workflows/
│       ├── README.md
│       ├── ark-agent-query-basic.json
│       └── ark-agent-query-with-params.json
└── docs/
    └── content/
        ├── integrations/
        │   └── n8n.mdx
        └── reference/
            └── ark-apis.mdx (updated)
```

### 11.2 Environment Variables

**n8n:**
```env
N8N_HOST=n8n.default.127.0.0.1.nip.io
N8N_PORT=5678
N8N_PROTOCOL=http
WEBHOOK_URL=http://n8n.default.127.0.0.1.nip.io:8080
GENERIC_TIMEZONE=America/New_York
N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true
N8N_RUNNERS_ENABLED=true
ARK_API_URL=http://ark-api.default.svc.cluster.local:8000
```

**ARK API:**
```env
AUTH_MODE=open  # or "sso" for production
OIDC_ISSUER_URL=https://auth.example.com  # if AUTH_MODE=sso
OIDC_APPLICATION_ID=ark-api  # if AUTH_MODE=sso
```

### 11.3 Glossary

- **n8n**: Low-code workflow automation platform
- **ARK**: Agentic Runtime for Kubernetes
- **CRD**: Custom Resource Definition (Kubernetes)
- **Query CR**: Kubernetes custom resource representing agent query
- **Execute Endpoint**: Simplified API for agent execution
- **HTTPRoute**: Gateway API resource for routing
- **PVC**: PersistentVolumeClaim (Kubernetes storage)
- **SSE**: Server-Sent Events (streaming protocol)
- **OIDC**: OpenID Connect (authentication)
- **JWT**: JSON Web Token (authentication)

### 11.4 References

- n8n Documentation: https://docs.n8n.io
- ARK Documentation: /docs
- Kubernetes Gateway API: https://gateway-api.sigs.k8s.io
- OpenAPI Specification: /openapi.json

---

**Document Version:** 1.0
**Last Updated:** 2024-01-01
**Authors:** ARK Development Team
**Status:** Complete - Implementation Done
