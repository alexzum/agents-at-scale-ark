/* Copyright 2025. McKinsey & Company */

package genai

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/client-go/tools/record"
	"sigs.k8s.io/controller-runtime/pkg/client"
	logf "sigs.k8s.io/controller-runtime/pkg/log"
	a2aclient "trpc.group/trpc-go/trpc-a2a-go/client"
	"trpc.group/trpc-go/trpc-a2a-go/protocol"

	arkv1prealpha1 "mckinsey.com/ark/api/v1prealpha1"
	"mckinsey.com/ark/internal/telemetry"
)

// DiscoverA2AAgents discovers agents from an A2A server using simplified HTTP approach
// Note: The A2A library doesn't provide a direct agent discovery API yet, so we use HTTP
func DiscoverA2AAgents(ctx context.Context, k8sClient client.Client, address string, headers []arkv1prealpha1.Header, namespace string) (*A2AAgentCard, error) {
	return DiscoverA2AAgentsWithRecorder(ctx, k8sClient, address, headers, namespace, nil, nil)
}

// DiscoverA2AAgentsWithRecorder discovers agents with optional K8s event recording
func DiscoverA2AAgentsWithRecorder(ctx context.Context, k8sClient client.Client, address string, headers []arkv1prealpha1.Header, namespace string, recorder record.EventRecorder, obj client.Object) (*A2AAgentCard, error) {
	// Use protocol constant for agent card path
	agentCardURL := strings.TrimSuffix(address, "/") + protocol.AgentCardPath

	// Create HTTP client with consistent timeout and configuration
	var clientOptions []a2aclient.Option
	clientOptions = append(clientOptions, a2aclient.WithTimeout(30*time.Second))

	// Resolve headers and create custom request handler if needed
	if len(headers) > 0 {
		resolvedHeaders, err := resolveA2AHeaders(ctx, k8sClient, headers, namespace)
		if err != nil {
			return nil, err
		}

		clientOptions = append(clientOptions, a2aclient.WithHTTPReqHandler(&customA2ARequestHandler{
			headers: resolvedHeaders,
		}))
	}

	// Create A2A client (even though we only use it for consistent HTTP handling)
	_, err := a2aclient.NewA2AClient(address, clientOptions...)
	if err != nil {
		if recorder != nil && obj != nil {
			recorder.Event(obj, corev1.EventTypeWarning, "A2AClientCreateFailed", fmt.Sprintf("Failed to create A2A client for %s: %v", address, err))
		}
		return nil, fmt.Errorf("failed to create A2A client: %w", err)
	}

	// For now, perform direct HTTP GET since library doesn't expose agent discovery
	// This maintains consistency with A2A client configuration
	httpClient := &http.Client{Timeout: 30 * time.Second}

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, agentCardURL, nil)
	if err != nil {
		if recorder != nil && obj != nil {
			recorder.Event(obj, corev1.EventTypeWarning, "A2ARequestCreateFailed", fmt.Sprintf("Failed to create HTTP request to %s: %v", agentCardURL, err))
		}
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Add headers if specified
	if len(headers) > 0 {
		resolvedHeaders, err := resolveA2AHeaders(ctx, k8sClient, headers, namespace)
		if err != nil {
			if recorder != nil && obj != nil {
				recorder.Event(obj, corev1.EventTypeWarning, "A2AHeaderResolutionFailed", fmt.Sprintf("Failed to resolve A2A headers: %v", err))
			}
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
		if recorder != nil && obj != nil {
			recorder.Event(obj, corev1.EventTypeWarning, "A2AConnectionFailed", fmt.Sprintf("Failed to connect to A2A server %s: %v", address, err))
		}
		return nil, fmt.Errorf("failed to connect to A2A server: %w", err)
	}
	defer func() {
		if closeErr := resp.Body.Close(); closeErr != nil {
			logf.FromContext(ctx).Error(closeErr, "failed to close response body")
		}
	}()

	if resp.StatusCode != http.StatusOK {
		if recorder != nil && obj != nil {
			recorder.Event(obj, corev1.EventTypeWarning, "A2ABadResponse", fmt.Sprintf("A2A server %s returned HTTP status %d", address, resp.StatusCode))
		}
		return nil, fmt.Errorf("A2A server returned status %d", resp.StatusCode)
	}

	// Parse agent card using official library types
	var agentCard A2AAgentCard
	if err := json.NewDecoder(resp.Body).Decode(&agentCard); err != nil {
		if recorder != nil && obj != nil {
			recorder.Event(obj, corev1.EventTypeWarning, "A2AParseError", fmt.Sprintf("Failed to parse agent card from %s: %v", address, err))
		}
		return nil, fmt.Errorf("failed to parse agent card: %w", err)
	}

	if recorder != nil && obj != nil {
		recorder.Event(obj, corev1.EventTypeNormal, "A2ADiscoverySuccess", fmt.Sprintf("Successfully discovered agent %s from %s", agentCard.Name, address))
	}

	return &agentCard, nil
}

// ExecuteA2AAgent executes a task on an A2A agent using the official library client
func ExecuteA2AAgent(ctx context.Context, k8sClient client.Client, address string, headers []arkv1prealpha1.Header, namespace, input, agentName string) (string, error) {
	return ExecuteA2AAgentWithRecorder(ctx, k8sClient, address, headers, namespace, input, agentName, nil, nil)
}

// ExecuteA2AAgentWithRecorder executes a task on an A2A agent with optional K8s event recording
func ExecuteA2AAgentWithRecorder(ctx context.Context, k8sClient client.Client, address string, headers []arkv1prealpha1.Header, namespace, input, agentName string, recorder record.EventRecorder, obj client.Object) (string, error) {
	// Create A2A client with options
	rpcURL := strings.TrimSuffix(address, "/")
	logf.FromContext(ctx).Info("calling A2A server", "url", rpcURL)

	// Resolve headers first
	var clientOptions []a2aclient.Option
	if len(headers) > 0 {
		resolvedHeaders, err := resolveA2AHeaders(ctx, k8sClient, headers, namespace)
		if err != nil {
			if recorder != nil && obj != nil {
				recorder.Event(obj, corev1.EventTypeWarning, "A2AHeaderResolutionFailed", fmt.Sprintf("Failed to resolve headers for agent %s: %v", agentName, err))
			}
			return "", err
		}

		// Create custom HTTP client with headers and OTEL tracing
		httpClient := &http.Client{Timeout: 30 * time.Second}
		clientOptions = append(clientOptions, a2aclient.WithHTTPClient(httpClient))

		// Use custom request handler to add headers and OTEL tracing
		clientOptions = append(clientOptions, a2aclient.WithHTTPReqHandler(&customA2ARequestHandler{
			headers: resolvedHeaders,
		}))
	}

	// Create client
	a2aClient, err := a2aclient.NewA2AClient(rpcURL, clientOptions...)
	if err != nil {
		if recorder != nil && obj != nil {
			recorder.Event(obj, corev1.EventTypeWarning, "A2AClientCreateFailed", fmt.Sprintf("Failed to create A2A client for agent %s at %s: %v", agentName, rpcURL, err))
		}
		return "", fmt.Errorf("failed to create A2A client: %w", err)
	}

	// Create message using protocol constructors
	message := protocol.NewMessage(protocol.MessageRoleUser, []protocol.Part{
		protocol.NewTextPart(input),
	})

	// Create parameters
	params := protocol.SendMessageParams{
		RPCID:   protocol.GenerateRPCID(),
		Message: message,
	}

	// Send message using library API - replaces 100+ lines of manual HTTP/JSON-RPC handling
	result, err := a2aClient.SendMessage(ctx, params)
	if err != nil {
		if recorder != nil && obj != nil {
			recorder.Event(obj, corev1.EventTypeWarning, "A2AExecutionFailed", fmt.Sprintf("A2A agent %s execution failed at %s: %v", agentName, rpcURL, err))
		}
		return "", fmt.Errorf("A2A server call failed: %w", err)
	}

	// Use proper type assertions instead of manual parsing
	response, err := extractTextFromMessageResult(result)
	if err != nil {
		if recorder != nil && obj != nil {
			recorder.Event(obj, corev1.EventTypeWarning, "A2AResponseParseError", fmt.Sprintf("Failed to parse response from agent %s: %v", agentName, err))
		}
		return "", err
	}

	if recorder != nil && obj != nil {
		recorder.Event(obj, corev1.EventTypeNormal, "A2AExecutionSuccess", fmt.Sprintf("Successfully executed agent %s, response length: %d characters", agentName, len(response)))
	}

	return response, nil
}

// customA2ARequestHandler handles adding custom headers and OTEL tracing to A2A requests
type customA2ARequestHandler struct {
	headers map[string]string
}

// Handle implements the HTTPReqHandler interface
func (h *customA2ARequestHandler) Handle(ctx context.Context, httpClient *http.Client, req *http.Request) (*http.Response, error) {
	// Add custom headers
	for name, value := range h.headers {
		req.Header.Set(name, value)
	}

	// Inject OTEL trace context and session headers
	headerMap := make(map[string]string)
	telemetry.InjectOTELHeaders(ctx, headerMap)
	for name, value := range headerMap {
		req.Header.Set(name, value)
	}

	// Perform the request
	return httpClient.Do(req)
}

// extractTextFromMessageResult extracts text from MessageResult using type-safe methods
func extractTextFromMessageResult(result *protocol.MessageResult) (string, error) {
	if result == nil {
		return "", fmt.Errorf("result is nil")
	}

	switch r := result.Result.(type) {
	case *protocol.Message:
		text := extractTextFromParts(r.Parts)
		logf.Log.Info("A2A message extracted", "text", text, "parts_count", len(r.Parts))
		return text, nil
	case *protocol.Task:
		return "", fmt.Errorf("received task response, streaming not yet supported")
	default:
		return "", fmt.Errorf("unexpected result type: %T", result.Result)
	}
}

// extractTextFromParts extracts text from message parts in a type-safe way
func extractTextFromParts(parts []protocol.Part) string {
	var text strings.Builder
	for i, part := range parts {
		logf.Log.Info("A2A part debug", "index", i, "part_type", fmt.Sprintf("%T", part))
		if textPart, ok := part.(protocol.TextPart); ok {
			logf.Log.Info("A2A text part found", "text", textPart.Text)
			text.WriteString(textPart.Text)
		} else if textPartPtr, ok := part.(*protocol.TextPart); ok {
			logf.Log.Info("A2A text part pointer found", "text", textPartPtr.Text)
			text.WriteString(textPartPtr.Text)
		} else {
			logf.Log.Info("A2A non-text part skipped", "part_type", fmt.Sprintf("%T", part))
		}
	}
	return text.String()
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
