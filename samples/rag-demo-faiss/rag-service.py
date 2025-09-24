#!/usr/bin/env python3
"""
FAISS-based RAG service for ARK agents
Provides vector embedding, indexing, and semantic retrieval
"""

import os
import json
import faiss
import numpy as np
from typing import List, Dict, Any
from dataclasses import dataclass
from openai import OpenAI
from flask import Flask, request, jsonify
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Document:
    id: str
    content: str
    metadata: Dict[str, Any] = None

class FAISSRAGService:
    def __init__(self, embedding_model: str = "text-embedding-3-small"):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        )
        self.embedding_model = embedding_model
        self.dimension = 1536  # text-embedding-3-small dimension

        # Initialize FAISS index
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product (cosine similarity)
        self.documents: List[Document] = []
        self.doc_id_to_index: Dict[str, int] = {}

        logger.info(f"Initialized RAG service with {embedding_model}")

    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text using OpenAI API"""
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            embedding = np.array(response.data[0].embedding, dtype=np.float32)
            # Normalize for cosine similarity
            embedding = embedding / np.linalg.norm(embedding)
            return embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            raise

    def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """Add document to the vector store"""
        try:
            # Get embedding
            embedding = self.get_embedding(content)

            # Add to FAISS index
            self.index.add(embedding.reshape(1, -1))

            # Store document
            doc = Document(id=doc_id, content=content, metadata=metadata or {})
            doc_index = len(self.documents)
            self.documents.append(doc)
            self.doc_id_to_index[doc_id] = doc_index

            logger.info(f"Added document {doc_id} to index (total: {len(self.documents)})")
            return True
        except Exception as e:
            logger.error(f"Error adding document {doc_id}: {e}")
            return False

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        try:
            if len(self.documents) == 0:
                return []

            # Get query embedding
            query_embedding = self.get_embedding(query)

            # Search FAISS index
            scores, indices = self.index.search(query_embedding.reshape(1, -1), min(top_k, len(self.documents)))

            # Format results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.documents):
                    doc = self.documents[idx]
                    results.append({
                        "id": doc.id,
                        "content": doc.content,
                        "score": float(score),
                        "metadata": doc.metadata
                    })

            logger.info(f"Search for '{query}' returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []

    def load_knowledge_base(self, file_path: str) -> bool:
        """Load documents from a text file (one document per line)"""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                line = line.strip()
                if line:
                    doc_id = f"doc_{i+1}"
                    self.add_document(doc_id, line, {"line_number": i+1})

            logger.info(f"Loaded {len(lines)} documents from {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            return False

# Flask API
app = Flask(__name__)
rag_service = FAISSRAGService()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "documents": len(rag_service.documents)})

@app.route('/add_document', methods=['POST'])
def add_document():
    data = request.json
    doc_id = data.get('id')
    content = data.get('content')
    metadata = data.get('metadata', {})

    if not doc_id or not content:
        return jsonify({"error": "Missing id or content"}), 400

    success = rag_service.add_document(doc_id, content, metadata)
    return jsonify({"success": success})

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query')
    top_k = data.get('top_k', 3)

    if not query:
        return jsonify({"error": "Missing query"}), 400

    results = rag_service.search(query, top_k)
    return jsonify({"results": results})

@app.route('/load_file', methods=['POST'])
def load_file():
    data = request.json
    file_path = data.get('file_path')

    if not file_path:
        return jsonify({"error": "Missing file_path"}), 400

    success = rag_service.load_knowledge_base(file_path)
    return jsonify({"success": success, "document_count": len(rag_service.documents)})

if __name__ == '__main__':
    # Load initial knowledge base if provided
    kb_file = os.getenv('KNOWLEDGE_BASE_FILE')
    if kb_file and os.path.exists(kb_file):
        rag_service.load_knowledge_base(kb_file)

    app.run(host='0.0.0.0', port=8000, debug=True)