# Memory System Messages Test Cases

This test suite provides comprehensive testing for memory functionality in ARK, specifically focusing on system message handling and message delivery verification using mock-llm.

## Test Overview

The test suite includes the following test cases:

### 1. Basic Memory Message Delivery (`a06-query.yaml`)
- **Purpose**: Verifies that memory messages are correctly passed to the LLM
- **What it tests**: 
  - Memory messages are retrieved and sent to the LLM
  - Agent's system prompt is included
  - Previous conversation history is accessible
- **Assertions**: 
  - Query completes successfully
  - Response contains memory content
  - Response contains system prompt
  - Response contains previous conversation references

### 2. System Prompt Behavior (`a07-query-system-prompt.yaml`)
- **Purpose**: Tests the `memorySystemMessageParameter` functionality
- **What it tests**:
  - Whether the agent's current system prompt is used
  - How the `memorySystemMessageParameter` affects behavior
- **Assertions**:
  - Query completes successfully
  - Response contains current system prompt
  - Response shows the memorySystemMessageParameter value

### 3. Session Continuity (`a08-query-continuity.yaml`)
- **Purpose**: Tests multiple queries in the same session
- **What it tests**:
  - Memory persistence across queries
  - Conversation flow continuity
  - All messages are properly delivered
- **Assertions**:
  - Query completes successfully
  - Response contains previous discussion
  - Response shows conversation flow
  - Response contains all messages

### 4. No System Prompt Test (`a09-query-no-system-prompt.yaml`)
- **Purpose**: Tests behavior when `memorySystemMessageParameter` is set to `false`
- **What it tests**:
  - Only current system prompt is used (not from memory)
  - Memory messages are still included
  - Parameter behavior is correctly applied
- **Assertions**:
  - Query completes successfully
  - Response contains only current system prompt
  - Response shows memorySystemMessageParameter as false
  - Response contains memory messages

### 5. Mock-LLM Message Delivery (`a10-query-mock-llm.yaml`)
- **Purpose**: Directly tests what messages are sent to the LLM
- **What it tests**:
  - Exact message content sent to LLM
  - Message order and structure
  - System message inclusion
  - Memory message inclusion
- **Assertions**:
  - Query completes successfully
  - Response contains mock response
  - Response contains system message
  - Response contains user message
  - Response contains memory messages
  - Response shows correct message order

## Mock-LLM Configuration

The test uses a mock-llm server that:
- Echoes back all messages sent to it
- Uses JMESPath to extract message content
- Returns a structured response showing exactly what was sent
- Allows verification of message delivery and content

## Key Features Tested

### Memory System Message Parameter
The `memorySystemMessageParameter` controls whether:
- `true`: Use the original system prompt from memory (if available)
- `false`: Always use the agent's current system prompt

### Message Flow
The test verifies the correct message flow:
1. Agent's system prompt (based on `memorySystemMessageParameter`)
2. Memory messages (conversation history)
3. Current user input

### Session Management
Tests verify that:
- Memory persists across queries in the same session
- Conversation history is maintained
- New messages are added to memory after each query

## Running the Tests

```bash
# Run all memory system message tests
chainsaw test tests/memory-system-messages/

# Run specific test
chainsaw test tests/memory-system-messages/ --test-name memory-system-messages

# Run with debug output
chainsaw test tests/memory-system-messages/ --skip-delete
```

## Expected Behavior

### With `memorySystemMessageParameter: true`
- Agent's current system prompt is used
- Memory messages are included
- Previous conversation context is available

### With `memorySystemMessageParameter: false`
- Only agent's current system prompt is used
- Memory messages are still included
- Previous conversation context is available

### Mock-LLM Response
The mock-llm will return a response containing:
- All messages sent to it (system, memory, user)
- Message order and structure
- Content verification for testing

## Troubleshooting

### Common Issues
1. **Memory service not available**: Ensure ark-cluster-memory is running
2. **Mock-llm not responding**: Check mock-llm deployment and service
3. **Memory data not populated**: Verify memory data setup script
4. **Assertions failing**: Check that mock-llm is returning expected format

### Debug Steps
1. Check mock-llm logs: `kubectl logs deployment/mock-llm`
2. Verify memory service: `kubectl get memory test-memory`
3. Check query status: `kubectl get query memory-test-query`
4. Review mock-llm response format

## Future Enhancements

This test suite can be extended to test:
- Different memory backends
- Complex conversation flows
- Memory cleanup and TTL
- Cross-session memory isolation
- Memory performance and scaling
