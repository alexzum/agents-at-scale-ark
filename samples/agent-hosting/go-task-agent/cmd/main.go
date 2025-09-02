package main

import (
	"flag"
	"fmt"
	"go-task-agent/internal/agent"
	"log"
	"net/http"
	"os"
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

	// Create agent handler
	handler := agent.NewHandler()

	// Setup HTTP server
	addr := fmt.Sprintf("%s:%d", *host, *port)
	
	log.Printf("🔥 GO AGENT: Starting Go Task-Based A2A server on %s", addr)
	log.Printf("Available endpoints:")
	log.Printf("  - /.well-known/agent.json (agent discovery)")
	log.Printf("  - /.well-known/agent-card.json (modern agent discovery)")
	log.Printf("  - / (main JSONRPC endpoint)")
	log.Printf("  - /health (health check)")
	log.Printf("")
	log.Printf("This agent returns task structures directly using Go and trpc-a2a-go patterns")
	log.Printf("to demonstrate proper handling of task vs message responses.")

	if err := http.ListenAndServe(addr, handler); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}