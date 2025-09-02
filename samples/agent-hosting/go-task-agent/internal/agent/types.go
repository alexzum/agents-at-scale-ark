package agent

import (
	"time"
)

// TaskPart represents a part of a task artifact
type TaskPart struct {
	Kind string `json:"kind"`
	Text string `json:"text"`
}

// TaskArtifact represents an artifact in a task
type TaskArtifact struct {
	ArtifactID string     `json:"artifactId"`
	Parts      []TaskPart `json:"parts"`
}

// TaskStatus represents the status of a task
type TaskStatus struct {
	State     string    `json:"state"`
	Timestamp time.Time `json:"timestamp"`
}

// HistoryMessage represents a message in task history
type HistoryMessage struct {
	ContextID string                 `json:"contextId"`
	Kind      string                 `json:"kind"`
	MessageID string                 `json:"messageId"`
	Metadata  map[string]interface{} `json:"metadata"`
	Parts     []TaskPart             `json:"parts"`
	Role      string                 `json:"role"`
	TaskID    string                 `json:"taskId"`
}

// TaskResponse represents the complete task response structure
type TaskResponse struct {
	Artifacts        []TaskArtifact    `json:"artifacts"`
	ContextID        string            `json:"contextId"`
	History          []HistoryMessage  `json:"history"`
	ID               string            `json:"id"`
	Kind             string            `json:"kind"`
	Status           TaskStatus        `json:"status"`
	ValidationErrors []interface{}     `json:"validation_errors"`
}

// AgentCapabilities represents what the agent can do
type AgentCapabilities struct {
	Streaming bool `json:"streaming"`
}

// AgentSkill represents a skill the agent has
type AgentSkill struct {
	ID           string   `json:"id"`
	Name         string   `json:"name"`
	Description  string   `json:"description"`
	Tags         []string `json:"tags"`
	Examples     []string `json:"examples"`
	InputModes   []string `json:"inputModes"`
	OutputModes  []string `json:"outputModes"`
}

// AgentCard represents the agent's metadata
type AgentCard struct {
	Name                   string              `json:"name"`
	Description            string              `json:"description"`
	URL                    string              `json:"url"`
	Version                string              `json:"version"`
	DefaultInputModes      []string            `json:"defaultInputModes"`
	DefaultOutputModes     []string            `json:"defaultOutputModes"`
	Capabilities           AgentCapabilities   `json:"capabilities"`
	Skills                 []AgentSkill        `json:"skills"`
	ProtocolVersion        string              `json:"protocolVersion"`
	PreferredTransport     string              `json:"preferredTransport,omitempty"`
}

// MessageRequest represents an incoming message request
type MessageRequest struct {
	JSONRPC string `json:"jsonrpc"`
	ID      int    `json:"id"`
	Method  string `json:"method"`
	Params  struct {
		Message struct {
			MessageID string `json:"messageId"`
			Role      string `json:"role"`
			Parts     []struct {
				Kind string `json:"kind"`
				Text string `json:"text"`
			} `json:"parts"`
		} `json:"message"`
	} `json:"params"`
}

// JSONRPCRequest represents a generic JSONRPC request
type JSONRPCRequest struct {
	JSONRPC string      `json:"jsonrpc"`
	ID      interface{} `json:"id"`
	Method  string      `json:"method"`
	Params  interface{} `json:"params"`
}

// JSONRPCResponse represents a JSONRPC response
type JSONRPCResponse struct {
	JSONRPC string      `json:"jsonrpc"`
	ID      interface{} `json:"id"`
	Result  interface{} `json:"result,omitempty"`
	Error   interface{} `json:"error,omitempty"`
}