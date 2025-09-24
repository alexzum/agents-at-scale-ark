#!/bin/bash

echo "🧹 Cleaning up RAG demo..."

# Stop RAG service
if [ -f .rag_service.pid ]; then
    PID=$(cat .rag_service.pid)
    echo "🛑 Stopping RAG service (PID: $PID)..."
    kill $PID 2>/dev/null || echo "   Process already stopped"
    rm .rag_service.pid
fi

# Remove ARK resources
echo "🗑️  Removing ARK resources..."
kubectl delete -f test-rag-query.yaml --ignore-not-found
kubectl delete -f hr-assistant-rag.yaml --ignore-not-found
kubectl delete -f rag-search-tool.yaml --ignore-not-found

echo "✅ Cleanup complete!"