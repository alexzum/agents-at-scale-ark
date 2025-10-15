#!/bin/bash

# Script to start simple-agent and register with ARK
set -e

echo "🚀 Starting Simple Agent A2A Server..."

# Change to simple-agent directory
cd "$(dirname "$0")"

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Installing dependencies..."
    make init
fi

# Start the server in background
echo "🔄 Starting A2A server..."
make dev &
SERVER_PID=$!

# Wait for server to be ready
echo "⏳ Waiting for server to start..."
sleep 5

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Server failed to start"
    exit 1
fi

echo "✅ A2A server is running on port 8000"

# Create A2AServer resource
echo "🔗 Registering with ARK..."
kubectl apply -f - <<EOF
apiVersion: ark.mckinsey.com/v1prealpha1
kind: A2AServer
metadata:
  name: simple-agent
spec:
  address:
    value: "http://host.docker.internal:8000"
  description: "Simple agent with conversation, math, and echo capabilities"
EOF

echo "✅ Simple Agent registered with ARK!"
echo "🎯 Test with: fark agent simple-agent-simple-agent 'Hello!'"

# Keep the script running to maintain the server
wait $SERVER_PID
