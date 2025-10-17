# Delete Functionality Tests

This directory contains comprehensive test cases for the delete API and CLI functionality added in the `feat/delete-query` branch.

## Overview

The delete functionality includes:

### API Delete Endpoints
- **Agents**: `DELETE /v1/agents/{agent_name}`
- **Models**: `DELETE /v1/models/{model_name}`
- **Tools**: `DELETE /v1/tools/{tool_name}`
- **Teams**: `DELETE /v1/teams/{team_name}`
- **Queries**: `DELETE /v1/queries/{query_name}`
- **A2A Servers**: `DELETE /v1/a2a-servers/{a2a_server_name}`
- **MCP Servers**: `DELETE /v1/mcp-servers/{mcp_server_name}`
- **Sessions**: `DELETE /v1/sessions/{session_id}`, `DELETE /v1/sessions` (all), `DELETE /v1/sessions/{session_id}/queries/{query_id}/messages`
- **Memories**: `DELETE /v1/memories/{name}`
- **Evaluators**: `DELETE /v1/evaluators/{name}`
- **Evaluations**: `DELETE /v1/evaluations/{name}`
- **Secrets**: `DELETE /v1/secrets/{secret_name}`

### CLI Delete Commands
- **Memory Management**: 
  - `ark memory reset session <sessionId>` - Delete a specific session
  - `ark memory reset query <sessionId> <queryId>` - Delete messages for a specific query
  - `ark memory reset all` - Delete all sessions and their messages
  - `ark memory list` - List all sessions

## Test Structure

### 1. Chainsaw Integration Tests (`chainsaw-test.yaml`)
End-to-end integration tests that:
- Create test resources (models, agents, tools, teams, queries)
- Test API delete endpoints
- Test CLI memory commands
- Verify proper deletion and error handling
- Clean up resources

### 2. Bash Test Script (`test-delete-api-cli.sh`)
Comprehensive test script that covers:
- **API Tests**: All delete endpoints with proper status code validation
- **CLI Tests**: Memory management commands
- **Error Handling**: Non-existent resources, invalid namespaces
- **Integration Tests**: Cascade effects, active queries
- **Performance Tests**: Delete operation timing

### 3. Test Manifests (`manifests/`)
Kubernetes resources used for testing:
- `a00-rbac.yaml` - RBAC configuration
- `a01-secret.yaml` - Test secret for API keys
- `a02-model.yaml` - Test model resource
- `a03-agent.yaml` - Test agent resource
- `a04-tool.yaml` - Test tool resource
- `a05-team.yaml` - Test team resource
- `a06-query.yaml` - Test query resource

## Running the Tests

### Prerequisites
- ARK API service running and accessible
- ARK CLI installed and configured
- kubectl configured with cluster access
- curl, bc, and other standard tools

### Run Chainsaw Tests
```bash
cd tests/delete-functionality
chainsaw test .
```

### Run Bash Test Script
```bash
cd tests/delete-functionality
chmod +x test-delete-api-cli.sh
./test-delete-api-cli.sh
```

### Run Specific Test Categories
```bash
# API tests only
./test-delete-api-cli.sh | grep "API Delete Tests" -A 20

# CLI tests only
./test-delete-api-cli.sh | grep "CLI Delete Tests" -A 10

# Error handling tests only
./test-delete-api-cli.sh | grep "Error Handling Tests" -A 10
```

## Test Coverage

### API Delete Tests
- ✅ Model deletion and verification
- ✅ Agent deletion and verification
- ✅ Tool deletion and verification
- ✅ Team deletion and verification
- ✅ Query deletion and verification
- ✅ Session deletion (individual and bulk)
- ✅ Query message deletion
- ✅ Non-existent resource handling (404 responses)
- ✅ Invalid namespace handling

### CLI Delete Tests
- ✅ Memory session deletion
- ✅ Memory query message deletion
- ✅ Memory bulk deletion (all sessions)
- ✅ Memory listing functionality
- ✅ Error handling for invalid session/query IDs

### Integration Tests
- ✅ Cascade effect testing (deleting dependencies)
- ✅ Active query handling during agent deletion
- ✅ Performance testing (timing validation)

### Error Handling Tests
- ✅ Non-existent resource deletion (404 responses)
- ✅ Invalid namespace parameter handling
- ✅ Network error handling
- ✅ Authentication error handling

## Expected Behavior

### Successful Deletions
- API endpoints return `204 No Content` status
- Resources are completely removed from the cluster
- Subsequent GET requests return `404 Not Found`
- CLI commands complete without errors

### Error Cases
- Non-existent resources return `404 Not Found`
- Invalid namespaces return `404 Not Found`
- Network errors are properly handled and reported
- CLI commands fail gracefully with appropriate error messages

### Performance Expectations
- Individual resource deletions complete within 5 seconds
- Bulk operations (5 resources) complete within 10 seconds
- Memory operations complete within 2 seconds

## Troubleshooting

### Common Issues
1. **API Connection Errors**: Ensure ARK API service is running and accessible
2. **CLI Command Failures**: Verify ARK CLI is installed and configured
3. **Resource Creation Failures**: Check RBAC permissions and resource dependencies
4. **Timeout Errors**: Increase timeout values in test configuration

### Debug Mode
Enable debug output by setting environment variables:
```bash
export DEBUG=true
export VERBOSE=true
./test-delete-api-cli.sh
```

### Log Collection
For debugging, collect logs from:
- ARK API service: `kubectl logs -l app=ark-api -n default`
- ARK Controller: `kubectl logs -l app.kubernetes.io/name=ark-controller -n ark-system`
- Test namespace events: `kubectl get events -n <test-namespace>`

## Contributing

When adding new delete functionality:
1. Add corresponding test cases to both Chainsaw and bash test scripts
2. Update test manifests if new resource types are added
3. Update this README with new test coverage
4. Ensure all tests pass before submitting PR

## Related Documentation
- [ARK API Documentation](../../docs/content/api-reference/)
- [ARK CLI Documentation](../../docs/content/cli-reference/)
- [Testing Guide](../../docs/content/developer-guide/testing.mdx)
