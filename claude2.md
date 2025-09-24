# ARK YAML Configuration Learnings

## Model Configuration

**Working format:**
```yaml
apiVersion: ark.mckinsey.com/v1alpha1
kind: Model
metadata:
  name: model-name
  namespace: default
spec:
  config:
    azure:
      apiKey:
        valueFrom:
          secretKeyRef:
            key: token
            name: azure-openai-secret
      apiVersion:
        value: "2024-10-21"
      baseUrl:
        value: https://openai.prod.ai-gateway.quantumblack.com/80948656-dd10-4633-be49-4ebd6c302368/v1
  model:
    value: gpt-4o-mini
  type: azure
```

## Agent Configuration

**Working format (no execution engine):**
```yaml
apiVersion: ark.mckinsey.com/v1alpha1
kind: Agent
metadata:
  name: agent-name
  namespace: default
spec:
  modelRef:
    name: working-model-name
  prompt: Your agent prompt here
  tools: []
```

**Key Learning:** Agents work better WITHOUT explicitly specifying execution engine. Let ARK use defaults.

## Query Configuration

```yaml
apiVersion: ark.mckinsey.com/v1alpha1
kind: Query
metadata:
  name: query-name
  namespace: default
spec:
  input: "Your question here"
  targets:
  - name: agent-name
    type: agent
  timeout: 5m
  ttl: 720h
```

## Common Issues

1. **Execution Engine:** Don't specify `executionEngine` in agent spec - let ARK handle defaults
2. **Model Phase Error:** Check secret token format and API endpoints
3. **Missing Executors:** Run `make executor-langchain-install` if needed
4. **Secret Format:** Use `token` key in azure-openai-secret