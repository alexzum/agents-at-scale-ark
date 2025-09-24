# FAISS-based RAG for ARK Agents

A complete implementation of semantic search using FAISS vector embeddings integrated with ARK agents.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   ARK Agent     │───▶│   rag-search     │───▶│  FAISS RAG      │
│  (hr-assistant) │    │      Tool        │    │   Service       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  Vector Store   │
                                                │ (FAISS + OpenAI)│
                                                └─────────────────┘
```

## Features

- **Vector Embeddings**: OpenAI text-embedding-3-small
- **Semantic Search**: FAISS IndexFlatIP (cosine similarity)
- **REST API**: Flask service with health checks
- **ARK Integration**: Custom tool for agent access
- **Auto-loading**: Loads knowledge base on startup

## Quick Start

```bash
# Set OpenAI API key
export OPENAI_API_KEY="your-openai-api-key"

# Run setup
cd samples/rag-demo-faiss
./setup.sh

# Test the system
kubectl apply -f test-rag-query.yaml
kubectl get query test-rag-semantics -w
```

## Components

### 1. RAG Service (`rag-service.py`)
- FAISS vector store with 1536-dimensional embeddings
- OpenAI embedding API integration
- REST endpoints: `/search`, `/add_document`, `/load_file`
- Automatic knowledge base loading

### 2. ARK Tool (`rag-search-tool.yaml`)
- HTTP tool for semantic search
- Configurable top-k results
- JSON request/response format

### 3. Agent (`hr-assistant-rag.yaml`)
- RAG-enabled HR assistant
- Semantic search integration
- Policy-grounded responses

### 4. Knowledge Base (`company-policies.txt`)
- 10-line company policy document
- One policy per line for clear chunking
- Remote work, meetings, equipment policies

## API Endpoints

### Search Documents
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "remote work days", "top_k": 3}'
```

### Add Document
```bash
curl -X POST http://localhost:8000/add_document \
  -H "Content-Type: application/json" \
  -d '{"id": "policy_11", "content": "New policy text"}'
```

### Health Check
```bash
curl http://localhost:8000/health
```

## Testing

The test query asks about:
- Remote work day limits
- Equipment support
- Meeting requirements

Expected behavior:
1. Agent calls `rag-search` with relevant queries
2. RAG service returns semantically similar policies
3. Agent synthesizes information into helpful response

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: Required for embeddings
- `OPENAI_BASE_URL`: Optional, defaults to OpenAI
- `KNOWLEDGE_BASE_FILE`: Auto-load file path

### Customization
- **Embedding Model**: Change `embedding_model` in `FAISSRAGService`
- **Vector Dimension**: Adjust `dimension` for different models
- **Similarity Metric**: Modify FAISS index type
- **Chunk Size**: Edit knowledge base file format

## Cleanup

```bash
./cleanup.sh
```

Removes all ARK resources and stops the RAG service.

## Extending the System

### Add More Documents
```python
# Via API
curl -X POST http://localhost:8000/add_document \
  -d '{"id": "new_doc", "content": "Document text"}'

# Via file
echo "New policy line" >> company-policies.txt
# Restart service to reload
```

### Different Embedding Models
```python
# In rag-service.py
rag_service = FAISSRAGService(embedding_model="text-embedding-3-large")
```

### Multiple Knowledge Bases
Extend the service to support multiple FAISS indices for different domains (HR, Engineering, Legal, etc.).

## Troubleshooting

**Service won't start:**
- Check OpenAI API key is set
- Verify Python dependencies installed
- Check port 8000 is available

**No search results:**
- Verify knowledge base loaded: `curl http://localhost:8000/health`
- Check embedding API connectivity
- Try broader search terms

**Agent not using tool:**
- Verify tool is deployed: `kubectl get tool rag-search`
- Check agent references correct tool name
- Review agent logs for tool call errors