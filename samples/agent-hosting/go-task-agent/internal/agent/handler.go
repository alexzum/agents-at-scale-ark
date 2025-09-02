package agent

import (
	"crypto/tls"
	"encoding/json"
	"fmt"
	"go-task-agent/internal/weather"
	"log"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/google/uuid"
)

// TaskState represents the current state of a task
type TaskState struct {
	ID          string
	StartTime   time.Time
	State       string
	WeatherText string
	MessageID   string
	CallbackURL string
}

// Handler handles HTTP requests for the agent
type Handler struct {
	weatherClient *weather.Client
	agentCard     *AgentCard
	tasks         map[string]*TaskState
	tasksMutex    sync.RWMutex
	httpClient    *http.Client
}

// NewHandler creates a new agent handler
func NewHandler() *Handler {
	// Create HTTP client that can handle self-signed certificates if needed
	httpClient := &http.Client{
		Timeout: 30 * time.Second,
	}
	
	// Check if we should skip TLS verification (for development/testing)
	if os.Getenv("SKIP_TLS_VERIFY") == "true" {
		log.Printf("🔥 GO AGENT: TLS verification disabled (SKIP_TLS_VERIFY=true)")
		httpClient.Transport = &http.Transport{
			TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
		}
	} else {
		log.Printf("🔥 GO AGENT: TLS verification enabled (SKIP_TLS_VERIFY not set)")
	}

	// Create agent card with localhost URL for port forwarding
	agentCard := &AgentCard{
		Name:        "go_task_weather_reporter",
		Description: "Go weather agent that returns task structures using trpc-a2a-go patterns",
		URL:         "http://localhost:8085/",
		Version:     "1.0.0",
		DefaultInputModes:  []string{"text/plain"},
		DefaultOutputModes: []string{"application/json"},
		Capabilities: AgentCapabilities{
			Streaming: false,
		},
		Skills: []AgentSkill{
			{
				ID:          "go_task_weather_forecast",
				Name:        "Go Task-Based Weather Forecast",
				Description: "Weather forecasting that returns task structures instead of messages",
				Tags:        []string{"weather", "forecast", "task", "go", "debug"},
				Examples:    []string{"weather in London", "how is the weather in Tokyo", "forecast for Paris"},
				InputModes:  []string{"text/plain"},
				OutputModes: []string{"application/json"},
			},
		},
		ProtocolVersion:    "0.3.0",
		PreferredTransport: "JSONRPC",
	}

	return &Handler{
		weatherClient: weather.NewClient(),
		agentCard:     agentCard,
		tasks:         make(map[string]*TaskState),
		httpClient:    httpClient,
	}
}

// ServeHTTP implements http.Handler
func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	switch r.URL.Path {
	case "/.well-known/agent.json":
		h.handleAgentCard(w, r)
	case "/.well-known/agent-card.json":
		h.handleAgentCard(w, r)
	case "/health":
		h.handleHealth(w, r)
	case "/":
		if r.Method == "POST" {
			h.handleJSONRPC(w, r)
		} else {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		}
	default:
		http.NotFound(w, r)
	}
}

// handleAgentCard returns the agent card
func (h *Handler) handleAgentCard(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(h.agentCard)
}

// handleHealth returns health status
func (h *Handler) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status":     "healthy",
		"agent_type": "go_task_based",
	})
}

// handleJSONRPC handles JSONRPC requests
func (h *Handler) handleJSONRPC(w http.ResponseWriter, r *http.Request) {
	// Parse the JSONRPC request
	var jsonrpcReq JSONRPCRequest
	if err := json.NewDecoder(r.Body).Decode(&jsonrpcReq); err != nil {
		log.Printf("Error decoding JSONRPC request: %v", err)
		http.Error(w, "Bad request", http.StatusBadRequest)
		return
	}

	log.Printf("🔥 GO AGENT: Received JSONRPC method: %s", jsonrpcReq.Method)

	// Route based on method - ALWAYS create tasks for testing
	switch jsonrpcReq.Method {
	case "message/send", "task/submit":
		h.handleTaskSubmit(w, r, jsonrpcReq)
	case "task/status":
		h.handleTaskStatus(w, r, jsonrpcReq)
	default:
		// For any unknown method, also create a task (no immediate responses)
		log.Printf("🔥 GO AGENT: Unknown method %s - creating task anyway for testing", jsonrpcReq.Method)
		h.handleTaskSubmit(w, r, jsonrpcReq)
	}
}

// handleTaskSubmit handles task submission (both message/send and task/submit)
// ALWAYS creates a task instead of immediate response to test task parsing in ARK
func (h *Handler) handleTaskSubmit(w http.ResponseWriter, r *http.Request, jsonrpcReq JSONRPCRequest) {
	log.Printf("🔥 GO AGENT: Received %s request - ALWAYS creating task for testing", jsonrpcReq.Method)

	// Extract message text from params
	messageText := h.extractMessageText(jsonrpcReq.Params)
	log.Printf("🔥 GO AGENT: Extracted message text: %s", messageText)
	
	// Extract callback URL from params
	callbackURL := h.extractCallbackURL(jsonrpcReq.Params)
	log.Printf("🔥 GO AGENT: Extracted callback URL: %s", callbackURL)

	// Extract only the last user message to avoid conversation history accumulation
	lastUserMessage := h.extractLastUserMessage(messageText)
	log.Printf("🔥 GO AGENT: Extracted last user message: %s", lastUserMessage)

	// Get weather result (prepare it in advance)
	weatherResult, err := h.weatherClient.GetWeather(lastUserMessage)
	if err != nil {
		log.Printf("Error getting weather: %v", err)
		weatherResult = fmt.Sprintf("Error getting weather: %v", err)
	}

	// Create new task in submitted state
	taskID := uuid.New().String()
	messageID := h.extractMessageID(jsonrpcReq.Params)
	
	h.tasksMutex.Lock()
	h.tasks[taskID] = &TaskState{
		ID:          taskID,
		StartTime:   time.Now(),
		State:       "submitted",
		WeatherText: weatherResult,
		MessageID:   messageID,
		CallbackURL: callbackURL,
	}
	h.tasksMutex.Unlock()

	log.Printf("🔥 GO AGENT: Created task %s in submitted state (20s delay for testing)", taskID)

	// Start task processing in background with callback support
	if callbackURL != "" {
		go h.processTaskWithCallback(taskID, callbackURL, weatherResult)
	}

	// Return task in submitted state - ARK controller will need to poll for completion
	taskResponse := h.createTaskResponseWithState(taskID, messageID, "submitted", "Task submitted for weather processing - will complete in 20 seconds")

	response := JSONRPCResponse{
		JSONRPC: "2.0",
		ID:      jsonrpcReq.ID,
		Result:  taskResponse,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleTaskStatus handles task status polling
func (h *Handler) handleTaskStatus(w http.ResponseWriter, r *http.Request, jsonrpcReq JSONRPCRequest) {
	// Extract task ID from params
	params, ok := jsonrpcReq.Params.(map[string]interface{})
	if !ok {
		http.Error(w, "Invalid params", http.StatusBadRequest)
		return
	}

	taskID, ok := params["task_id"].(string)
	if !ok {
		http.Error(w, "Missing task_id", http.StatusBadRequest)
		return
	}

	log.Printf("🔥 GO AGENT: Checking status for task %s", taskID)

	// Get task state
	h.tasksMutex.RLock()
	taskState, exists := h.tasks[taskID]
	h.tasksMutex.RUnlock()

	if !exists {
		http.Error(w, "Task not found", http.StatusNotFound)
		return
	}

	// Calculate current state based on elapsed time
	elapsed := time.Since(taskState.StartTime)
	currentState := taskState.State
	messageText := "Task submitted for weather processing"

	if elapsed >= 10*time.Second {
		// After 20 seconds: completed
		currentState = "completed"
		messageText = taskState.WeatherText
	} else if elapsed >= 3*time.Second {
		// After 3 seconds: working
		currentState = "working"
		messageText = "Processing weather request..."
	} else {
		// Before 3 seconds: submitted
		currentState = "submitted"
		messageText = "Task submitted for weather processing"
	}

	log.Printf("🔥 GO AGENT: Task %s state: %s (elapsed: %v)", taskID, currentState, elapsed)

	// Create task response with current state
	taskResponse := h.createTaskResponseWithState(taskID, taskState.MessageID, currentState, messageText)

	response := JSONRPCResponse{
		JSONRPC: "2.0",
		ID:      jsonrpcReq.ID,
		Result:  taskResponse,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}


// extractMessageText extracts message text from JSONRPC params
func (h *Handler) extractMessageText(params interface{}) string {
	if params == nil {
		return "default weather query"
	}

	paramsMap, ok := params.(map[string]interface{})
	if !ok {
		return "default weather query"
	}

	// Try to extract from message.parts
	if message, ok := paramsMap["message"].(map[string]interface{}); ok {
		if parts, ok := message["parts"].([]interface{}); ok && len(parts) > 0 {
			if part, ok := parts[0].(map[string]interface{}); ok {
				if text, ok := part["text"].(string); ok {
					return text
				}
			}
		}
	}

	// Try direct input field
	if input, ok := paramsMap["input"].(string); ok {
		return input
	}

	return "default weather query"
}

// extractCallbackURL extracts callback URL from JSONRPC params
func (h *Handler) extractCallbackURL(params interface{}) string {
	if params == nil {
		return ""
	}

	paramsMap, ok := params.(map[string]interface{})
	if !ok {
		return ""
	}

	// Try to extract callbackUrl directly from params
	if callbackURL, ok := paramsMap["callbackUrl"].(string); ok {
		return callbackURL
	}

	return ""
}

// processTaskWithCallback handles task lifecycle and calls callback when completed
func (h *Handler) processTaskWithCallback(taskID, callbackURL, weatherResult string) {
	log.Printf("🔥 GO AGENT: Starting background processing for task %s with callback %s", taskID, callbackURL)

	contextID := "8f09994a-aad3-4e7d-91ef-6e8c231b3443"
	
	// Update to working state
	h.tasksMutex.Lock()
	if task, exists := h.tasks[taskID]; exists {
		task.State = "working"
		log.Printf("🔥 GO AGENT: Task %s moved to working state", taskID)
	}
	h.tasksMutex.Unlock()
	
	// Wait 5 seconds then send first intermediate task update
	time.Sleep(5 * time.Second)
	h.sendTaskUpdateWithMessage(callbackURL, taskID, contextID, "1f60a637-34b5-4f37-9282-f8a35cb57c4e", "Executing function `get_coordinates` - result: [32.78306, -96.80667]", "working")

	// Wait another 5 seconds then send second intermediate task update
	time.Sleep(5 * time.Second)
	h.sendTaskUpdateWithMessage(callbackURL, taskID, contextID, "0f4b6aa0-52ab-462d-a0fe-fa10f857b23c", "Executing function `weather_forecast` - result: Temperature: 37.0°C, Windspeed: 9.1 km/h", "working")

	// Wait another 5 seconds then send final completed task
	time.Sleep(5 * time.Second)

	// Update to completed state
	h.tasksMutex.Lock()
	if task, exists := h.tasks[taskID]; exists {
		task.State = "completed"
		log.Printf("🔥 GO AGENT: Task %s completed - calling callback", taskID)
	}
	h.tasksMutex.Unlock()

	// Send final completed task with artifact
	h.sendCompletedTaskWithArtifact(callbackURL, taskID, contextID, "77663cfa-c99c-4372-9412-415184d26de0", "The weather in Dallas is currently 37.0°C with a wind speed of 9.1 km/h.")
}

// sendTaskUpdateWithMessage sends a task update with an agent message in the history
func (h *Handler) sendTaskUpdateWithMessage(callbackURL, taskID, contextID, messageID, text, status string) {
	if callbackURL == "" {
		log.Printf("🔥 GO AGENT: No callback URL for task %s", taskID)
		return
	}

	// Create full task payload with running status and agent message in history
	payload := map[string]interface{}{
		"kind":      "task",
		"id":        taskID,
		"contextId": contextID,
		"artifacts": []interface{}{
			map[string]interface{}{
				"parts": []map[string]interface{}{
					{
						"text": text,
					},
				},
			},
		},
		"status": map[string]interface{}{
			"state":     status,
			"timestamp": time.Now().Format(time.RFC3339Nano),
		},
		"history": []map[string]interface{}{
			{
				"contextId": contextID,
				"kind":      "message",
				"messageId": "msg-1756421253750-v9pvq2rnf",
				"metadata": map[string]interface{}{
					"user_id": "",
				},
				"parts": []map[string]interface{}{
					{
						"kind": "text",
						"text": "how is the weather in dallas?",
					},
				},
				"role":   "user",
				"taskId": taskID,
			},
			{
				"contextId": contextID,
				"kind":      "message",
				"messageId": messageID,
				"parts": []map[string]interface{}{
					{
						"kind": "text",
						"text": text,
					},
				},
				"role":   "agent",
				"taskId": taskID,
			},
		},
		"validation_errors": []interface{}{},
	}

	h.sendPayload(callbackURL, taskID, payload, "task update with message")
}

// sendCompletedTaskWithArtifact sends the final completed task with artifact
func (h *Handler) sendCompletedTaskWithArtifact(callbackURL, taskID, contextID, artifactID, text string) {
	if callbackURL == "" {
		log.Printf("🔥 GO AGENT: No callback URL for task %s", taskID)
		return
	}

	// Create final completed task payload with artifact
	payload := map[string]interface{}{
		"kind":      "task",
		"id":        taskID,
		"contextId": contextID,
		"artifacts": []map[string]interface{}{
			{
				"artifactId": artifactID,
				"parts": []map[string]interface{}{
					{
						"kind": "text",
						"text": text,
					},
				},
			},
		},
		"status": map[string]interface{}{
			"state":     "completed",
			"timestamp": time.Now().Format(time.RFC3339Nano),
		},
		"history": []map[string]interface{}{
			{
				"contextId": contextID,
				"kind":      "message",
				"messageId": "msg-1756421253750-v9pvq2rnf",
				"metadata": map[string]interface{}{
					"user_id": "",
				},
				"parts": []map[string]interface{}{
					{
						"kind": "text",
						"text": "how is the weather in dallas?",
					},
				},
				"role":   "user",
				"taskId": taskID,
			},
			{
				"contextId": contextID,
				"kind":      "message",
				"messageId": "1f60a637-34b5-4f37-9282-f8a35cb57c4e",
				"parts": []map[string]interface{}{
					{
						"kind": "text",
						"text": "Executing function `get_coordinates` - result: [32.78306, -96.80667]",
					},
				},
				"role":   "agent",
				"taskId": taskID,
			},
			{
				"contextId": contextID,
				"kind":      "message",
				"messageId": "0f4b6aa0-52ab-462d-a0fe-fa10f857b23c",
				"parts": []map[string]interface{}{
					{
						"kind": "text",
						"text": "Executing function `weather_forecast` - result: Temperature: 37.0°C, Windspeed: 9.1 km/h",
					},
				},
				"role":   "agent",
				"taskId": taskID,
			},
		},
		"validation_errors": []interface{}{},
	}

	h.sendPayload(callbackURL, taskID, payload, "completed task with artifact")
}

// sendPayload sends a JSON payload to the callback URL
func (h *Handler) sendPayload(callbackURL, taskID string, payload map[string]interface{}, payloadType string) {
	// Marshal payload
	payloadBytes, err := json.Marshal(payload)
	if err != nil {
		log.Printf("🔥 GO AGENT: Error marshaling %s payload for task %s: %v", payloadType, taskID, err)
		return
	}

	// Send HTTP POST to callback URL
	log.Printf("🔥 GO AGENT: Sending %s to callback URL %s for task %s", payloadType, callbackURL, taskID)
	
	resp, err := h.httpClient.Post(callbackURL, "application/json", strings.NewReader(string(payloadBytes)))
	if err != nil {
		log.Printf("🔥 GO AGENT: Error sending %s callback for task %s: %v", payloadType, taskID, err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		log.Printf("🔥 GO AGENT: Successfully sent %s callback for task %s (status: %d)", payloadType, taskID, resp.StatusCode)
	} else {
		log.Printf("🔥 GO AGENT: %s callback returned non-200 status for task %s: %d", payloadType, taskID, resp.StatusCode)
	}
}

// callCallback sends completion notification to callback URL
func (h *Handler) callCallback(callbackURL, taskID, weatherResult string) {
	if callbackURL == "" {
		log.Printf("🔥 GO AGENT: No callback URL for task %s", taskID)
		return
	}

	// Create callback payload
	payload := map[string]interface{}{
		"task_id": taskID,
		"status":  "completed",
		"artifacts": []map[string]interface{}{
			{
				"artifactId": uuid.New().String(),
				"parts": []map[string]interface{}{
					{
						"kind": "text",
						"text": weatherResult,
					},
				},
			},
		},
	}

	// Marshal payload
	payloadBytes, err := json.Marshal(payload)
	if err != nil {
		log.Printf("🔥 GO AGENT: Error marshaling callback payload for task %s: %v", taskID, err)
		return
	}

	// Send HTTP POST to callback URL
	log.Printf("🔥 GO AGENT: Calling callback URL %s for task %s", callbackURL, taskID)
	
	resp, err := h.httpClient.Post(callbackURL, "application/json", strings.NewReader(string(payloadBytes)))
	if err != nil {
		log.Printf("🔥 GO AGENT: Error calling callback for task %s: %v", taskID, err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		log.Printf("🔥 GO AGENT: Successfully called callback for task %s (status: %d)", taskID, resp.StatusCode)
	} else {
		log.Printf("🔥 GO AGENT: Callback returned non-200 status for task %s: %d", taskID, resp.StatusCode)
	}
}

// extractMessageID extracts message ID from JSONRPC params
func (h *Handler) extractMessageID(params interface{}) string {
	if params == nil {
		return "default-message-id"
	}

	paramsMap, ok := params.(map[string]interface{})
	if !ok {
		return "default-message-id"
	}

	if message, ok := paramsMap["message"].(map[string]interface{}); ok {
		if msgID, ok := message["messageId"].(string); ok {
			return msgID
		}
	}

	return "default-message-id"
}

// extractLastUserMessage extracts only the last user message from conversation history
func (h *Handler) extractLastUserMessage(fullText string) string {
	// If the text contains conversation history, extract only the last "User: " message
	lines := strings.Split(fullText, "\n")
	var lastUserMessage string
	
	for i := len(lines) - 1; i >= 0; i-- {
		line := strings.TrimSpace(lines[i])
		if strings.HasPrefix(line, "User: ") {
			lastUserMessage = strings.TrimPrefix(line, "User: ")
			break
		}
	}
	
	// If no "User: " prefix found, return the original text (for single messages)
	if lastUserMessage == "" {
		return fullText
	}
	
	return lastUserMessage
}

// createTaskResponseWithState creates a task response with specific state
func (h *Handler) createTaskResponseWithState(taskID, messageID, state, messageText string) *TaskResponse {
	contextID := uuid.New().String()

	var artifacts []TaskArtifact
	
	// Only populate artifacts for completed tasks
	if state == "completed" {
		artifactID := uuid.New().String()
		artifacts = []TaskArtifact{
			{
				ArtifactID: artifactID,
				Parts: []TaskPart{
					{
						Kind: "text",
						Text: messageText,
					},
				},
			},
		}
	}

	return &TaskResponse{
		Kind:      "task",
		ID:        taskID,
		ContextID: contextID,
		Artifacts: artifacts,
		Status: TaskStatus{
			State:     state,
			Timestamp: time.Now(),
		},
		History: []HistoryMessage{
			{
				ContextID: contextID,
				Kind:      "message",
				MessageID: fmt.Sprintf("msg-%d-%s", time.Now().UnixMilli(), uuid.New().String()[:8]),
				Metadata:  map[string]interface{}{"user_id": ""},
				Parts: []TaskPart{
					{
						Kind: "text",
						Text: "weather query",
					},
				},
				Role:   "user",
				TaskID: taskID,
			},
		},
		ValidationErrors: []interface{}{},
	}
}

