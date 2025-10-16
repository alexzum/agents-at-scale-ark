# Memory System Messages Test

Tests memory functionality with system messages using mock-llm to verify message delivery to the LLM.

## What it tests
- **Memory Message Delivery**: Verifies that memory messages are correctly passed to the LLM
- **System Prompt Handling**: Tests whether the agent's system prompt is included with memory messages
- **Message Order**: Ensures messages arrive at the LLM in the correct order
- **Session Continuity**: Tests multiple queries in the same session
- **Memory System Message Parameter**: Tests the parameter that controls whether original system prompt is used

## Running
```bash
chainsaw test
```

Validates that memory messages are correctly delivered to the LLM and that the system prompt behavior works as expected.
