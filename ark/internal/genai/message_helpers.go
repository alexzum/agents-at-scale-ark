/* Copyright 2025. McKinsey & Company */

package genai

import (
	"mckinsey.com/ark/internal/annotations"
)

// PrepareExecutionMessages separates the current message from context messages
// and combines with memory history for agent/team execution.
// This pattern is used when the last message in inputMessages should be treated
// as the current input, while all previous messages (from memory and input)
// serve as conversation context.
func PrepareExecutionMessages(inputMessages, memoryMessages []Message) (currentMessage Message, contextMessages []Message) {
	currentMessage = inputMessages[len(inputMessages)-1]
	contextMessages = make([]Message, 0, len(memoryMessages)+len(inputMessages)-1)
	contextMessages = append(contextMessages, memoryMessages...)
	contextMessages = append(contextMessages, inputMessages[:len(inputMessages)-1]...)
	return currentMessage, contextMessages
}

// PrepareModelMessages combines all messages for direct model execution.
// This pattern is used when all messages (memory + input) should be sent
// to the model as a continuous conversation history.
func PrepareModelMessages(inputMessages, memoryMessages []Message) []Message {
	allMessages := make([]Message, 0, len(memoryMessages)+len(inputMessages))
	allMessages = append(allMessages, memoryMessages...)
	allMessages = append(allMessages, inputMessages...)
	return allMessages
}

// PrepareNewMessagesForMemory combines input and response messages for memory storage.
// This pattern is used to save both the input messages and the generated response
// messages to memory after successful execution.
func PrepareNewMessagesForMemory(inputMessages, responseMessages []Message) []Message {
	newMessages := make([]Message, 0, len(inputMessages)+len(responseMessages))
	newMessages = append(newMessages, inputMessages...)
	newMessages = append(newMessages, responseMessages...)
	return newMessages
}

// PrepareAgentMessagesForMemory prepares messages for memory storage, including system message if agent has annotation.
// This checks if the agent has the MemoryIncludeHydrateSystemMessage annotation and includes the system message
// at the start of a new conversation (when existingMessages is empty).
func PrepareAgentMessagesForMemory(agent *Agent, existingMessages, inputMessages, responseMessages []Message) []Message {
	// Check if agent has annotation to include system message in memory
	if agent.Annotations != nil && agent.Annotations[annotations.MemoryIncludeHydrateSystemMessage] == "true" {
		// Only include system message if this is the start of conversation (no existing messages)
		if len(existingMessages) == 0 {
			// Get the resolved prompt for the system message
			systemMessage := NewSystemMessage(agent.Prompt)
			messagesToLog := make([]Message, 0, 1+len(inputMessages)+len(responseMessages))
			messagesToLog = append(messagesToLog, systemMessage)
			messagesToLog = append(messagesToLog, inputMessages...)
			messagesToLog = append(messagesToLog, responseMessages...)
			return messagesToLog
		}
	}

	// Standard memory storage: input + response messages
	return PrepareNewMessagesForMemory(inputMessages, responseMessages)
}

// PrepareTeamMessagesForMemory prepares messages for memory storage when executing a team,
// checking team members for the system message annotation.
func PrepareTeamMessagesForMemory(team *Team, existingMessages, inputMessages, responseMessages []Message) []Message {
	// Check team members for system message annotation
	for _, member := range team.Members {
		agent, ok := member.(*Agent)
		if !ok {
			continue
		}

		if agent.Annotations == nil {
			continue
		}

		if agent.Annotations[annotations.MemoryIncludeHydrateSystemMessage] != "true" {
			continue
		}

		// Only include system message if this is the start of conversation (no existing messages)
		if len(existingMessages) == 0 {
			// Include system message with prompt in memory logs
			systemMessage := NewSystemMessage(agent.Prompt)
			messagesToLog := make([]Message, 0, 1+len(inputMessages)+len(responseMessages))
			messagesToLog = append(messagesToLog, systemMessage)
			messagesToLog = append(messagesToLog, inputMessages...)
			messagesToLog = append(messagesToLog, responseMessages...)
			return messagesToLog
		}

		// Standard memory storage: input + response
		return PrepareNewMessagesForMemory(inputMessages, responseMessages)
	}

	// If no agent has the annotation, use standard memory storage
	return PrepareNewMessagesForMemory(inputMessages, responseMessages)
}
