#!/bin/bash
set -e

echo "🚀 Setting up FAISS-based RAG for ARK"

# Check dependencies
echo "📋 Checking dependencies..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi

# Create virtual environment
echo "🐍 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Check OpenAI credentials
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set"
    echo "   Set it with: export OPENAI_API_KEY='your-key-here'"
fi

# Start RAG service in background
echo "🔍 Starting RAG service..."
export KNOWLEDGE_BASE_FILE="company-policies.txt"
python3 rag-service.py &
RAG_PID=$!
echo "RAG service started with PID: $RAG_PID"

# Wait for service to start
sleep 3

# Test service health
echo "🏥 Testing service health..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ RAG service is healthy"
else
    echo "❌ RAG service failed to start"
    kill $RAG_PID 2>/dev/null || true
    exit 1
fi

# Deploy ARK resources
echo "🎯 Deploying ARK resources..."
kubectl apply -f rag-search-tool.yaml
kubectl apply -f hr-assistant-rag.yaml

# Wait for resources
echo "⏳ Waiting for resources to be ready..."
kubectl wait --for=condition=Ready tool/rag-search --timeout=30s
kubectl wait --for=condition=Ready agent/hr-assistant-rag --timeout=30s

echo "🎉 RAG system deployed successfully!"
echo ""
echo "📝 To test the system:"
echo "   kubectl apply -f test-rag-query.yaml"
echo "   kubectl logs -f query/test-rag-semantics"
echo ""
echo "🛑 To stop RAG service:"
echo "   kill $RAG_PID"

# Save PID for cleanup
echo $RAG_PID > .rag_service.pid