/* Copyright 2025. McKinsey & Company */

package genai

import (
	"trpc.group/trpc-go/trpc-a2a-go/protocol"
	"trpc.group/trpc-go/trpc-a2a-go/server"
)

// Use the official A2A library types
type (
	A2AAgentCard = server.AgentCard
	A2ASkill     = server.AgentSkill
)

// A2A JSON-RPC types for client calls
type A2ATaskSendParams struct {
	Message a2a.Message `json:"message"`
}

// Message/send params with required messageId
type A2AMessageSendParams struct {
	Message A2AMessageWithID `json:"message"`
}

type A2AMessageWithID struct {
	MessageID string               `json:"messageId"`
	Role      protocol.MessageRole `json:"role"`
	Parts     []protocol.Part      `json:"parts"`
}

type A2ATaskSendResponse struct {
	TaskID string `json:"taskId"`
}

type A2ATaskGetParams struct {
	TaskID string `json:"taskId"`
}

type A2ATaskGetResponse struct {
	Task protocol.Task `json:"task"`
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
