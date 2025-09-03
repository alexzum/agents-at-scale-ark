/* Copyright 2025. McKinsey & Company */

package genai

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"sigs.k8s.io/controller-runtime/pkg/client"
	logf "sigs.k8s.io/controller-runtime/pkg/log"
	"trpc.group/trpc-go/trpc-a2a-go/protocol"

	arkv1prealpha1 "mckinsey.com/ark/api/v1prealpha1"
	"mckinsey.com/ark/internal/telemetry"
)

const (
	textKind = protocol.KindText
)

// DiscoverA2AAgents discovers agents from an A2A server using the official library types
func DiscoverA2AAgents(ctx context.Context, k8sClient client.Client, address string, headers []arkv1prealpha1.Header, namespace string) (*A2AAgentCard, error) {
	// Build the agent card discovery URL
	agentCardURL := strings.TrimSuffix(address, "/") + "/.well-known/agent.json"

	// Create HTTP client with timeout
	httpClient := &http.Client{
		Timeout: 30 * time.Second,
	}

	// Create request
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, agentCardURL, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Add headers if specified
	if len(headers) > 0 {
		resolvedHeaders, err := resolveA2AHeaders(ctx, k8sClient, headers, namespace)
		if err != nil {
			return nil, err
		}
		for name, value := range resolvedHeaders {
			req.Header.Set(name, value)
		}
	}

	// Inject OTEL trace context and session headers
	headerMap := make(map[string]string)
	telemetry.InjectOTELHeaders(ctx, headerMap)
	for name, value := range headerMap {
		req.Header.Set(name, value)
	}

	// Make request
	resp, err := httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to A2A server: %w", err)
	}
	defer func() {
		if closeErr := resp.Body.Close(); closeErr != nil {
			logf.FromContext(ctx).Error(closeErr, "failed to close response body")
		}
	}()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("A2A server returned status %d", resp.StatusCode)
	}

	// Parse agent card using official library types
	var agentCard A2AAgentCard
	if err := json.NewDecoder(resp.Body).Decode(&agentCard); err != nil {
		return nil, fmt.Errorf("failed to parse agent card: %w", err)
	}

	return &agentCard, nil
}

// ExecuteA2AAgent executes a task on an A2A agent using JSON-RPC
func ExecuteA2AAgent(ctx context.Context, k8sClient client.Client, address string, headers []arkv1prealpha1.Header, namespace, input, agentName string) (string, error) {
	// Always use standard A2A endpoint
	rpcURL := strings.TrimSuffix(address, "/")

	// Log the actual URL we're calling for debugging
	logf.FromContext(ctx).Info("calling A2A server", "url", rpcURL)

	// Create the message using official library types
	message := protocol.Message{
		Role: protocol.MessageRoleUser,
		Parts: []protocol.Part{
			protocol.NewTextPart(input),
		},
		MessageID: protocol.GenerateMessageID(),
		Kind:      "message",
	}

	// Always use message/send by default
	jsonrpcReq := A2AJSONRPCRequest{
		JSONRPC: "2.0",
		Method:  "message/send",
		Params: A2AMessageSendParams{
			Message: A2AMessageWithID{
				MessageID: message.MessageID,
				Role:      message.Role,
				Parts:     message.Parts,
			},
		},
		ID: 1,
	}

	// Marshal request
	reqBody, err := json.Marshal(jsonrpcReq)
	if err != nil {
		return "", fmt.Errorf("failed to marshal JSON-RPC request: %w", err)
	}

	// Create HTTP client - timeout is controlled by the context
	httpClient := &http.Client{}

	// Create HTTP request
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, rpcURL, bytes.NewBuffer(reqBody))
	if err != nil {
		return "", fmt.Errorf("failed to create HTTP request: %w", err)
	}

	// Set headers
	req.Header.Set("Content-Type", "application/json")
	if len(headers) > 0 {
		resolvedHeaders, err := resolveA2AHeaders(ctx, k8sClient, headers, namespace)
		if err != nil {
			return "", err
		}
		for name, value := range resolvedHeaders {
			req.Header.Set(name, value)
		}
	}

	// Inject OTEL trace context and session headers
	headerMap := make(map[string]string)
	telemetry.InjectOTELHeaders(ctx, headerMap)
	for name, value := range headerMap {
		req.Header.Set(name, value)
	}

	// Make request
	resp, err := httpClient.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to connect to A2A server: %w", err)
	}
	defer func() {
		if closeErr := resp.Body.Close(); closeErr != nil {
			logf.FromContext(ctx).Error(closeErr, "failed to close response body")
		}
	}()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("A2A server returned HTTP status %d", resp.StatusCode)
	}

	// Parse JSON-RPC response
	var jsonrpcResp A2AJSONRPCResponse
	if err := json.NewDecoder(resp.Body).Decode(&jsonrpcResp); err != nil {
		return "", fmt.Errorf("failed to parse JSON-RPC response: %w", err)
	}

	// Check for JSON-RPC error
	if jsonrpcResp.Error != nil {
		return "", fmt.Errorf("A2A server returned error: %s (code %d)", jsonrpcResp.Error.Message, jsonrpcResp.Error.Code)
	}

	// Handle different A2A response types
	result, err := handleA2AResponse(ctx, jsonrpcResp.Result, address, headerMap)
	if err != nil {
		logf.FromContext(ctx).Error(err, "A2A response processing failed", "agent", agentName)
		return "", err
	}

	return result, nil
}

// handleA2AResponse handles different A2A response types (message, task)
func handleA2AResponse(ctx context.Context, result interface{}, serverURL string, headers map[string]string) (string, error) {
	// Handle immediate string responses
	if resultStr, ok := result.(string); ok {
		return resultStr, nil
	}

	resultMap, ok := result.(map[string]interface{})
	if !ok {
		return "", fmt.Errorf("response result is not a map or string")
	}

	// Scenario 1: Immediate message response
	if parts, ok := resultMap["parts"].([]interface{}); ok && len(parts) > 0 {
		return extractTextFromRawParts(parts)
	}

	// Scenario 2: Task response (multi-step)
	if kind, ok := resultMap["kind"].(string); ok && kind == "task" {
		return handleTaskResponse(ctx, resultMap, serverURL, headers)
	}

	return "", fmt.Errorf("unknown A2A response format")
}

// handleTaskResponse handles task-based responses with polling support
func handleTaskResponse(ctx context.Context, taskMap map[string]interface{}, serverURL string, headers map[string]string) (string, error) {
	// Extract task ID
	taskID, hasTaskID := taskMap["id"].(string)
	if !hasTaskID {
		return "", fmt.Errorf("task response missing task ID")
	}

	// Process task status using shared logic
	result, continuePolling, err := processTaskStatus(taskMap)
	if err != nil {
		return "", err
	}
	if !continuePolling {
		return result, nil
	}

	// Task is still in progress, poll for completion
	return pollTaskCompletion(ctx, taskID, serverURL, headers)
}

// pollTaskCompletion polls a task until completion with exponential backoff
func pollTaskCompletion(ctx context.Context, taskID, serverURL string, headers map[string]string) (string, error) {
	maxAttempts := 30 // Maximum polling attempts
	baseDelay := 1    // Base delay in seconds
	maxDelay := 30    // Maximum delay in seconds

	for attempt := 0; attempt < maxAttempts; attempt++ {
		// Calculate delay with exponential backoff
		delay := baseDelay * (1 << uint(attempt))
		if delay > maxDelay {
			delay = maxDelay
		}

		// Wait before polling (except first attempt)
		if attempt > 0 {
			select {
			case <-ctx.Done():
				return "", ctx.Err()
			case <-time.After(time.Duration(delay) * time.Second):
			}
		}

		// Poll task status
		result, err := pollTaskStatus(ctx, taskID, serverURL, headers)
		if err != nil {
			return "", fmt.Errorf("failed to poll task %s: %w", taskID, err)
		}

		// Check if task is complete
		if result != "" {
			return result, nil
		}
	}

	return "", fmt.Errorf("task %s did not complete within timeout", taskID)
}

// pollTaskStatus makes a single task status request
func pollTaskStatus(ctx context.Context, taskID, serverURL string, headers map[string]string) (string, error) {
	// Prepare task status request
	statusReq := A2AJSONRPCRequest{
		JSONRPC: "2.0",
		ID:      1,
		Method:  "task/status",
		Params: map[string]interface{}{
			"task_id": taskID,
		},
	}

	reqBody, err := json.Marshal(statusReq)
	if err != nil {
		return "", fmt.Errorf("failed to marshal task status request: %w", err)
	}

	// Create HTTP request
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, serverURL, bytes.NewBuffer(reqBody))
	if err != nil {
		return "", fmt.Errorf("failed to create task status request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	for name, value := range headers {
		req.Header.Set(name, value)
	}

	// Make request
	httpClient := &http.Client{Timeout: 30 * time.Second}
	resp, err := httpClient.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to poll task status: %w", err)
	}
	defer func() {
		if closeErr := resp.Body.Close(); closeErr != nil {
			logf.Log.Error(closeErr, "failed to close response body")
		}
	}()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("task status poll returned HTTP %d", resp.StatusCode)
	}

	// Parse response
	var jsonrpcResp A2AJSONRPCResponse
	if err := json.NewDecoder(resp.Body).Decode(&jsonrpcResp); err != nil {
		return "", fmt.Errorf("failed to parse task status response: %w", err)
	}

	if jsonrpcResp.Error != nil {
		return "", fmt.Errorf("task status error: %s", jsonrpcResp.Error.Message)
	}

	// Parse task status response
	return handleTaskStatusResponse(jsonrpcResp.Result)
}

// handleTaskStatusResponse processes task status polling response
func handleTaskStatusResponse(result interface{}) (string, error) {
	resultMap, ok := result.(map[string]interface{})
	if !ok {
		return "", fmt.Errorf("task status response is not a map")
	}

	// Process task status using shared logic
	statusResult, continuePolling, err := processTaskStatus(resultMap)
	if err != nil {
		return "", err
	}
	if continuePolling {
		// Return empty to continue polling
		return "", nil
	}
	return statusResult, nil
}

// processTaskStatus processes task status and returns result, continuePolling flag, and error
func processTaskStatus(taskMap map[string]interface{}) (string, bool, error) {
	// Check task status
	status, hasStatus := taskMap["status"].(map[string]interface{})
	if !hasStatus {
		return "", false, fmt.Errorf("task response missing status")
	}

	state, hasState := status["state"].(string)
	if !hasState {
		return "", false, fmt.Errorf("task status missing state field")
	}

	switch protocol.TaskState(state) {
	case protocol.TaskStateCompleted:
		// Task completed, extract artifacts
		if artifacts, ok := taskMap["artifacts"].([]interface{}); ok && len(artifacts) > 0 {
			result, err := extractTextFromArtifacts(artifacts)
			return result, false, err
		}
		return "", false, fmt.Errorf("completed task has no artifacts")

	case protocol.TaskStateFailed:
		// Task failed, extract error message
		errorMsg := extractTaskFailureMessage(status)
		return "", false, fmt.Errorf("task failed: %s", errorMsg)

	case protocol.TaskStateSubmitted, protocol.TaskStateWorking:
		// Task is still in progress
		return "", true, nil

	default:
		return "", false, fmt.Errorf("unknown task state: %s", state)
	}
}

// extractTaskFailureMessage extracts error message from failed task status
func extractTaskFailureMessage(status map[string]interface{}) string {
	if message, ok := status["message"].(map[string]interface{}); ok {
		if parts, ok := message["parts"].([]interface{}); ok {
			if errorText, err := extractTextFromParts(parts, true); err == nil {
				return errorText
			}
		}
	}
	return "no error message available"
}

// extractTextFromArtifacts extracts text from artifact interfaces
func extractTextFromArtifacts(artifacts []interface{}) (string, error) {
	var collectedText string
	for _, artifact := range artifacts {
		artifactMap, ok := artifact.(map[string]interface{})
		if !ok {
			continue
		}

		parts, ok := artifactMap["parts"].([]interface{})
		if !ok {
			continue
		}

		text, _ := extractTextFromParts(parts, false)
		collectedText += text
	}

	if collectedText == "" {
		return "", fmt.Errorf("no artifacts with text content found")
	}
	return collectedText, nil
}

// extractTextFromParts extracts text from parts array with optional strict error handling
func extractTextFromParts(parts []interface{}, strict bool) (string, error) {
	var collectedText string
	for i, part := range parts {
		partMap, ok := part.(map[string]interface{})
		if !ok {
			if strict {
				return "", fmt.Errorf("parts[%d] is not a map", i)
			}
			continue
		}

		// Check for kind == "text"
		kind, ok := partMap["kind"].(string)
		if !ok || kind != textKind {
			continue
		}

		// Extract the text field
		text, ok := partMap["text"].(string)
		if !ok {
			if strict {
				return "", fmt.Errorf("text field in parts[%d] is missing or not a string", i)
			}
			continue
		}

		collectedText += text
	}

	if strict && collectedText == "" {
		return "", fmt.Errorf("no parts with kind 'text' and valid text field found")
	}

	return collectedText, nil
}

// extractTextFromRawParts extracts text from raw parts interfaces (strict mode for compatibility)
func extractTextFromRawParts(parts []interface{}) (string, error) {
	return extractTextFromParts(parts, true)
}

// resolveA2AHeaders resolves header values from ValueSources
func resolveA2AHeaders(ctx context.Context, k8sClient client.Client, headers []arkv1prealpha1.Header, namespace string) (map[string]string, error) {
	resolvedHeaders := make(map[string]string)
	for _, header := range headers {
		headerValue, err := ResolveHeaderValueV1PreAlpha1(ctx, k8sClient, header, namespace)
		if err != nil {
			return nil, fmt.Errorf("failed to resolve header %s: %v", header.Name, err)
		}
		resolvedHeaders[header.Name] = headerValue
	}
	logf.FromContext(ctx).Info("a2a headers resolved", "headers_count", len(resolvedHeaders))
	return resolvedHeaders, nil
}
