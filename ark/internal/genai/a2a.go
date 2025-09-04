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

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"sigs.k8s.io/controller-runtime/pkg/client"
	logf "sigs.k8s.io/controller-runtime/pkg/log"
	"trpc.group/trpc-go/trpc-a2a-go/protocol"

	arkv1alpha1 "mckinsey.com/ark/api/v1alpha1"
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

	// NOTE: Response parsing is not yet fully implemented for all A2A protocol variants
	// Check the A2A documentation for implementation details and next steps
	// For message/send, the response should contain the immediate result
	if resultStr, ok := jsonrpcResp.Result.(string); ok {
		return resultStr, nil
	}

	return parseA2AResponse(jsonrpcResp.Result)
}

// parseA2AResponse parses the JSON response and extracts text from parts
func parseA2AResponse(result interface{}) (string, error) {
	// Parse the JSON response and extract out the text
	resultMap, ok := result.(map[string]interface{})
	if !ok {
		return "", fmt.Errorf("response result is not a map")
	}

	// Extract "parts" from the result
	parts, ok := resultMap["parts"].([]interface{})
	if !ok || len(parts) == 0 {
		return "", fmt.Errorf("parts is missing or not a non-empty list")
	}

	var collectedText string
	for i, part := range parts {
		partMap, ok := part.(map[string]interface{})
		if !ok {
			return "", fmt.Errorf("parts[%d] is not a map", i)
		}

		// Check for kind == "text"
		kind, ok := partMap["kind"].(string)
		if !ok || kind != "text" {
			continue
		}

		// Extract the text field
		text, ok := partMap["text"].(string)
		if !ok {
			return "", fmt.Errorf("text field in parts[%d] is missing or not a string", i)
		}

		collectedText += text
	}

	if collectedText == "" {
		return "", fmt.Errorf("no parts with kind 'text' and valid text field found")
	}

	return collectedText, nil
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
