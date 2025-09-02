package agent

import (
	"context"
	"fmt"
	"go-task-agent/internal/weather"
	"log"
	"strings"
	"time"

	"github.com/google/uuid"
	"trpc.group/trpc-go/trpc-a2a-go/protocol"
	"trpc.group/trpc-go/trpc-a2a-go/server"
	"trpc.group/trpc-go/trpc-a2a-go/taskmanager"
)

// A2AProcessor implements the MessageProcessor interface from trpc-a2a-go
// This replaces the old Handler struct
type A2AProcessor struct {
	weatherClient *weather.Client
	tasks         map[string]*TaskState
}

// NewA2AProcessor creates a new A2A message processor
func NewA2AProcessor() *A2AProcessor {
	return &A2AProcessor{
		weatherClient: weather.NewClient(),
		tasks:         make(map[string]*TaskState),
	}
}

// ProcessMessage implements the MessageProcessor interface
// This replaces the old handleTaskSubmit method
func (p *A2AProcessor) ProcessMessage(
	ctx context.Context,
	message protocol.Message,
	options taskmanager.ProcessOptions,
	handle taskmanager.TaskHandler,
) (*taskmanager.MessageProcessingResult, error) {
	// Extract text from the incoming message
	text := p.extractTextFromMessage(message)
	log.Printf("🔥 GO AGENT: Processing message: %s", text)

	// Extract only the last user message to avoid conversation history accumulation
	lastUserMessage := p.extractLastUserMessage(text)
	log.Printf("🔥 GO AGENT: Extracted last user message: %s", lastUserMessage)

	// Always create a task to maintain the original behavior
	// This ensures ARK controller sees tasks instead of immediate responses
	taskIDStr := uuid.New().String()
	taskID, err := handle.BuildTask(&taskIDStr, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to build task: %w", err)
	}
	
	// Store task state
	p.tasks[taskID] = &TaskState{
		ID:        taskID,
		StartTime: time.Now(),
		State:     "submitted",
	}

	log.Printf("🔥 GO AGENT: Created task %s in submitted state (20s delay for testing)", taskID)

	// Start background processing
	go p.processTaskInBackground(ctx, taskID, lastUserMessage, handle)

	// Create initial task response
	task := &protocol.Task{
		ID:        taskID,
		ContextID: handle.GetContextID(),
		Status: protocol.TaskStatus{
			State: protocol.TaskStateSubmitted,
		},
	}

	// Return task in submitted state - ARK controller will need to poll for completion
	return &taskmanager.MessageProcessingResult{
		Result: task,
	}, nil
}

// processTaskInBackground simulates the original task processing behavior
func (p *A2AProcessor) processTaskInBackground(ctx context.Context, taskID string, text string, handle taskmanager.TaskHandler) {
	log.Printf("🔥 GO AGENT: Starting background processing for task %s", taskID)

	// Update to working state after 3 seconds
	time.Sleep(3 * time.Second)
	if task, exists := p.tasks[taskID]; exists {
		task.State = "working"
		log.Printf("🔥 GO AGENT: Task %s moved to working state", taskID)
	}
	
	// Update task state to working
	workingMsg := protocol.NewMessage(
		protocol.MessageRoleAgent,
		[]protocol.Part{protocol.NewTextPart("Processing weather request...")},
	)
	handle.UpdateTaskState(&taskID, protocol.TaskStateWorking, &workingMsg)

	// Send first intermediate update after 5 seconds
	time.Sleep(2 * time.Second)
	coordinatesArtifact := protocol.Artifact{
		ArtifactID: uuid.New().String(),
		Parts: []protocol.Part{
			protocol.NewTextPart("Executing function `get_coordinates` - result: [32.78306, -96.80667]"),
		},
	}
	handle.AddArtifact(&taskID, coordinatesArtifact, false, true)

	// Send second intermediate update after another 5 seconds
	time.Sleep(5 * time.Second)
	weatherArtifact := protocol.Artifact{
		ArtifactID: uuid.New().String(),
		Parts: []protocol.Part{
			protocol.NewTextPart("Executing function `weather_forecast` - result: Temperature: 37.0°C, Windspeed: 9.1 km/h"),
		},
	}
	handle.AddArtifact(&taskID, weatherArtifact, false, true)

	// Complete after another 5 seconds
	time.Sleep(5 * time.Second)

	// Get weather result
	weatherResult, err := p.weatherClient.GetWeather(text)
	if err != nil {
		log.Printf("Error getting weather: %v", err)
		weatherResult = fmt.Sprintf("Error getting weather: %v", err)
	}

	// Update to completed state
	if task, exists := p.tasks[taskID]; exists {
		task.State = "completed"
		task.WeatherText = weatherResult
		log.Printf("🔥 GO AGENT: Task %s completed", taskID)
	}

	// Send final result as artifact
	finalArtifact := protocol.Artifact{
		ArtifactID: uuid.New().String(),
		Parts: []protocol.Part{
			protocol.NewTextPart(weatherResult),
		},
	}
	handle.AddArtifact(&taskID, finalArtifact, true, false)

	// Update task state to completed
	completedMsg := protocol.NewMessage(
		protocol.MessageRoleAgent,
		[]protocol.Part{protocol.NewTextPart("Weather forecast completed")},
	)
	handle.UpdateTaskState(&taskID, protocol.TaskStateCompleted, &completedMsg)
}

// extractTextFromMessage extracts text content from a protocol.Message
func (p *A2AProcessor) extractTextFromMessage(message protocol.Message) string {
	for _, part := range message.Parts {
		if textPart, ok := part.(*protocol.TextPart); ok {
			return textPart.Text
		}
	}
	return "default weather query"
}

// extractLastUserMessage extracts only the last user message from conversation history
func (p *A2AProcessor) extractLastUserMessage(fullText string) string {
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

// CreateAgentCard creates the agent card configuration
func CreateAgentCard(host string, port int) server.AgentCard {
	return server.AgentCard{
		Name:        "go_task_weather_reporter",
		Description: "Go weather agent that returns task structures using trpc-a2a-go patterns",
		URL:         fmt.Sprintf("http://localhost:%d/", port), // Keep localhost for port forwarding
		Version:     "2.0.0",
		Capabilities: server.AgentCapabilities{
			Streaming: boolPtr(true), // Now we support streaming through trpc-a2a-go
		},
		DefaultInputModes:  []string{protocol.KindText},
		DefaultOutputModes: []string{protocol.KindText, protocol.KindTask},
		Skills: []server.AgentSkill{
			{
				ID:          "go_task_weather_forecast",
				Name:        "Go Task-Based Weather Forecast",
				Description: stringPtr("Weather forecasting that returns task structures instead of messages"),
				Tags:        []string{"weather", "forecast", "task", "go", "debug", "trpc-a2a-go"},
				Examples:    []string{"weather in London", "how is the weather in Tokyo", "forecast for Paris"},
				InputModes:  []string{protocol.KindText},
				OutputModes: []string{protocol.KindText, protocol.KindTask},
			},
		},
		ProtocolVersion:    stringPtr("0.3.0"),
		PreferredTransport: stringPtr("JSONRPC"),
	}
}

// Helper function to create string pointers
func stringPtr(s string) *string {
	return &s
}

// Helper function to create bool pointers
func boolPtr(b bool) *bool {
	return &b
}