# n8n Workflow Templates for ARK

Sample n8n workflows demonstrating integration with ARK agents.

## Available Workflows

### `ark-agent-query-basic.json`
Basic workflow demonstrating agent query execution:
1. Manual trigger to start workflow
2. HTTP Request to list available agents
3. HTTP Request to execute agent query
4. Process and display results

### `ark-agent-query-with-params.json`
Advanced workflow with parameters:
1. Manual trigger with input parameters
2. Execute agent with custom parameters
3. Conditional routing based on response
4. Error handling

## Importing Workflows

1. Access n8n UI at http://n8n.default.127.0.0.1.nip.io:8080
2. Click on "Workflows" in the left sidebar
3. Click "Import from File" or "Import from URL"
4. Select the workflow JSON file
5. Configure the ARK API base URL if needed
6. Save and execute

## ARK API Configuration

The workflows use the following ARK API endpoints:

- **List Agents**: `GET http://ark-api.default.svc.cluster.local:8000/v1/agents`
- **Execute Agent**: `POST http://ark-api.default.svc.cluster.local:8000/v1/agents/{agent_name}/execute`

For in-cluster access (recommended), use:
```
http://ark-api.default.svc.cluster.local:8000
```

For external access (development):
```
http://ark-api.default.127.0.0.1.nip.io:8080
```

## Customization

Edit the HTTP Request nodes to:
- Change the ARK API base URL
- Modify query parameters
- Add authentication headers (when AUTH_MODE=sso)
- Adjust timeout values
- Add custom parameters

## Tips

- Use the "Execute Node" button to test individual nodes
- Check the execution log to debug issues
- Use the "Set" node to transform data between steps
- Add "IF" nodes for conditional logic
- Use "Code" nodes for complex data transformations
