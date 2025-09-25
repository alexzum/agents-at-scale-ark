# System Message Memory Control

## Overview

By default, ARK agents do **not** include system messages (prompts) in their conversation memory. This prevents cluttering the conversation history with repetitive system instructions and keeps memory focused on the actual conversation flow.

However, there are cases where you might want to include system messages in memory for debugging, auditing, or specific use cases.

## Default Behavior

**✅ System messages are NOT included in memory by default**

This means when you look at the memory section, you won't see system messages like:
- "You're a helpful assistant. Provide clear and concise answers."
- "You are a weather assistant..."
- "You are a research analyst..."

Only the actual conversation (user messages and assistant responses) are stored in memory.

## Optional Annotation

You can control whether system messages are included in memory using the following annotation:

```yaml
metadata:
  annotations:
    ark.mckinsey.com/include-system-message-in-memory: "true"
```

## Behavior Summary

- **Without annotation**: System messages are NOT included in memory ✅ (default)
- **With annotation set to "true"**: System messages ARE included in memory **only once at the start of a conversation**
- **With annotation set to "false" or any other value**: System messages are NOT included in memory

## Important: System Messages Logged Only Once

When the annotation is enabled, system messages are only included in memory **the first time each agent is executed in a session**. The system checks if there are any system messages in the conversation history that match the agent's prompt - if found, it means this agent has already been executed and the system message should not be included again.

This prevents duplicate system messages from cluttering the memory for subsequent executions of the same agent in the same session.

## Use Cases

### When to Include System Messages in Memory

1. **Debugging**: When troubleshooting agent behavior, having the system message in memory helps understand the context
2. **Auditing**: For compliance or audit purposes, you might need to track what instructions were given to the agent
3. **Analysis**: When analyzing conversation patterns, system messages provide important context
4. **Development**: During development and testing, including system messages helps verify agent configuration

### When NOT to Include System Messages in Memory (Default)

1. **Production**: In production environments, system messages typically don't add value to conversation history
2. **Token Efficiency**: System messages consume tokens in memory without providing conversational value
3. **Clean History**: Keeps conversation history focused on actual user-agent interactions

## Example

```yaml
apiVersion: ark.mckinsey.com/v1alpha1
kind: Agent
metadata:
  name: debug-agent
  annotations:
    ark.mckinsey.com/include-system-message-in-memory: "true"
spec:
  description: An agent that includes system messages in memory for debugging
  prompt: |
    You are a helpful assistant that includes its system message in memory.
    This helps with debugging and understanding the agent's behavior.
```

## Implementation Details

- The annotation is checked in both local execution and execution engine paths
- System messages are included at the beginning of the message sequence returned to memory
- **System messages are only included the first time each agent is executed in a session**
- The annotation only affects memory storage, not the actual LLM calls (system messages are always sent to the LLM)
- This feature works with all execution engines (local, external, A2A)
- **Prevents duplicate system messages** from being logged for each query in the same session

## Current Status

✅ **System messages are excluded from memory by default** - this is the correct behavior you wanted!

The annotation feature is available if you ever need to include system messages for debugging purposes.
