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
	// Check if system messages from this team's agents are already in existing messages
	hasTeamSystemMessages := false
	for _, member := range team.Members {
		agent, ok := member.(*Agent)
		if !ok {
			continue
		}

		if agent.Annotations == nil {
			continue
		}

		if agent.Annotations[annotations.MemoryIncludeHydrateSystemMessage] == "true" {
			agentSystemMessage := NewSystemMessage(agent.Prompt)
			if containsSystemMessage(existingMessages, agentSystemMessage) {
				hasTeamSystemMessages = true
				break
			}
		}
	}

	// If team system messages are already present, just store input + response
	if hasTeamSystemMessages {
		return PrepareNewMessagesForMemory(inputMessages, responseMessages)
	}

	// First time storing for this team - include system messages
	var systemMessages []Message
	for _, member := range team.Members {
		agent, ok := member.(*Agent)
		if !ok {
			continue
		}

		if agent.Annotations == nil {
			continue
		}

		if agent.Annotations[annotations.MemoryIncludeHydrateSystemMessage] == "true" {
			systemMessage := NewSystemMessage(agent.Prompt)
			systemMessages = append(systemMessages, systemMessage)
		}
	}

	// Include system messages + input + response
	if len(systemMessages) > 0 {
		messagesToLog := make([]Message, 0, len(systemMessages)+len(inputMessages)+len(responseMessages))
		messagesToLog = append(messagesToLog, systemMessages...)
		messagesToLog = append(messagesToLog, inputMessages...)
		messagesToLog = append(messagesToLog, responseMessages...)
		return messagesToLog
	}

	// No system messages to add
	return PrepareNewMessagesForMemory(inputMessages, responseMessages)
}

// containsSystemMessage checks if a system message is already present in the existing messages
func containsSystemMessage(existingMessages []Message, systemMessage Message) bool {
	for _, msg := range existingMessages {
		// Check if this is a system message
		if msg.OfSystem != nil {
			// Get the content from the system message
			var existingContent string
			if msg.OfSystem.Content.OfString.Value != "" {
				existingContent = msg.OfSystem.Content.OfString.Value
			}

			// Get the content from the system message we're checking
			var targetContent string
			if systemMessage.OfSystem != nil && systemMessage.OfSystem.Content.OfString.Value != "" {
				targetContent = systemMessage.OfSystem.Content.OfString.Value
			}

			// Compare the content
			if existingContent == targetContent {
				return true
			}
		}
	}
	return false
}
