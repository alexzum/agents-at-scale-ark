/* Copyright 2025. McKinsey & Company */

package genai

import "github.com/a2aserver/a2a-go"

// Use the official A2A library types
type (
	A2AAgentCard = a2a.AgentCard
	A2ASkill     = a2a.AgentSkill
)

// A2A JSON-RPC types for client calls
type A2ATaskSendParams struct {
	Message a2a.Message `json:"message"`
}

// Message/send params with required messageId
type A2AMessageSendParams struct {
	Message A2AMessageWithID `json:"message"`
}

// Task/submit params for long-running operations
type A2ATaskSubmitParams struct {
	Message A2AMessageWithID `json:"message"`
}

type A2AMessageWithID struct {
	MessageID string     `json:"messageId"`
	Role      a2a.Role   `json:"role"`
	Parts     []a2a.Part `json:"parts"`
}

type A2ATaskSendResponse struct {
	TaskID string `json:"taskId"`
}

type A2ATaskGetParams struct {
	TaskID string `json:"taskId"`
}

type A2ATaskGetResponse struct {
	Task a2a.Task `json:"task"`
}

type A2AJSONRPCRequest struct {
	JSONRPC string      `json:"jsonrpc"`
	Method  string      `json:"method"`
	Params  interface{} `json:"params"`
	ID      interface{} `json:"id"`
}

type A2AJSONRPCResponse struct {
	JSONRPC string      `json:"jsonrpc"`
	Result  interface{} `json:"result,omitempty"`
	Error   *A2AError   `json:"error,omitempty"`
	ID      interface{} `json:"id"`
}

type A2AError struct {
	Code    int         `json:"code"`
	Message string      `json:"message"`
	Data    interface{} `json:"data,omitempty"`
}
