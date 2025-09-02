package main

import (
	"flag"
	"fmt"
	"go-task-agent/internal/agent"
	"log"
	"os"
	"time"

	"trpc.group/trpc-go/trpc-a2a-go/server"
	"trpc.group/trpc-go/trpc-a2a-go/taskmanager"
)

func main() {
	var (
		host = flag.String("host", "0.0.0.0", "Host to bind to")
		port = flag.Int("port", 8082, "Port to bind to")
	)
	flag.Parse()

	// Check for required environment variables (placeholder)
	if os.Getenv("DEBUG") != "" {
		log.Println("Debug mode enabled")
	}

	// Create message processor
	processor := agent.NewA2AProcessor()

	// Create task manager with the processor
	taskManager, err := taskmanager.NewMemoryTaskManager(
		processor,
		taskmanager.WithConversationTTL(30*time.Second, 5*time.Minute),
	)
	if err != nil {
		log.Fatalf("Failed to create task manager: %v", err)
	}

	// Create agent card
	agentCard := agent.CreateAgentCard(*host, *port)

	// Create A2A server using trpc-a2a-go
	srv, err := server.NewA2AServer(
		agentCard,
		taskManager,
		server.WithCORSEnabled(true),
		server.WithIdleTimeout(1*time.Minute),
	)
	if err != nil {
		log.Fatalf("Failed to create A2A server: %v", err)
	}

	// Setup HTTP server
	addr := fmt.Sprintf("%s:%d", *host, *port)
	
	log.Printf("🔥 GO AGENT: Starting Go Task-Based A2A server on %s", addr)
	log.Printf("Available endpoints:")
	log.Printf("  - /.well-known/agent.json (agent discovery)")
	log.Printf("  - /.well-known/agent-card.json (modern agent discovery)")
	log.Printf("  - / (main JSONRPC endpoint)")
	log.Printf("  - /health (health check)")
	log.Printf("")
	log.Printf("This agent now uses trpc-a2a-go framework for proper A2A protocol handling")
	log.Printf("with built-in task management and streaming support.")

	if err := srv.Start(addr); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}