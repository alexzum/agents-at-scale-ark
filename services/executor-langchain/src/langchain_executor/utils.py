"""Shared utilities for LangChain executor."""

import logging
from pathlib import Path
from typing import List, Optional
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import SecretStr

logger = logging.getLogger(__name__)


def create_chat_client(model) -> ChatOpenAI:
    """Create a ChatOpenAI client based on the model configuration."""
    config = model.config
    
    if model.type == "azure":
        azure_config = config.get("azure", {})
        api_key = azure_config.get("apiKey", "")
        base_url = azure_config.get("baseUrl", "")
        api_version = azure_config.get("apiVersion", "")
        properties = azure_config.get("properties", {})
        
        if not api_key or not base_url:
            raise ValueError("Azure OpenAI requires apiKey and baseUrl")
        
        # Get properties with defaults
        temperature = float(properties.get("temperature", "0.7"))
        max_tokens = properties.get("max_tokens")
        top_p = properties.get("top_p")
        frequency_penalty = properties.get("frequency_penalty")
        presence_penalty = properties.get("presence_penalty")
        
        # Azure OpenAI: construct full deployment URL
        full_base_url = f"{base_url.rstrip('/')}/openai/deployments/{model.name}/"

        # Handle JWT tokens for enterprise Azure setups
        default_headers = {}
        if api_key.startswith("eyJ"):  # JWT token (starts with eyJ)
            # For JWT tokens, use api-key header like ARK controller
            default_headers["api-key"] = api_key
            # Still set api_key for LangChain compatibility
            api_key_param = api_key
        else:
            # Standard Azure API key
            api_key_param = api_key

        kwargs = {
            "model": model.name,
            "api_key": SecretStr(api_key_param),
            "base_url": full_base_url,
            "default_query": {"api-version": api_version} if api_version else {},
            "temperature": temperature,
        }

        # Add custom headers for JWT tokens
        if default_headers:
            kwargs["default_headers"] = default_headers
        
        if max_tokens:
            kwargs["max_tokens"] = int(max_tokens)
        if top_p:
            kwargs["top_p"] = float(top_p)
        if frequency_penalty:
            kwargs["frequency_penalty"] = float(frequency_penalty)
        if presence_penalty:
            kwargs["presence_penalty"] = float(presence_penalty)
        
        return ChatOpenAI(**kwargs)
        
    elif model.type == "openai":
        openai_config = config.get("openai", {})
        api_key = openai_config.get("apiKey", "")
        base_url = openai_config.get("baseUrl", "")
        properties = openai_config.get("properties", {})
        
        if not api_key:
            raise ValueError("OpenAI requires apiKey")
        
        # Get properties with defaults
        temperature = float(properties.get("temperature", "0.7"))
        max_tokens = properties.get("max_tokens")
        top_p = properties.get("top_p")
        frequency_penalty = properties.get("frequency_penalty")
        presence_penalty = properties.get("presence_penalty")
        
        kwargs = {
            "model": model.name,
            "api_key": SecretStr(api_key),
            "base_url": base_url or None,
            "temperature": temperature,
        }
        
        if max_tokens:
            kwargs["max_tokens"] = int(max_tokens)
        if top_p:
            kwargs["top_p"] = float(top_p)
        if frequency_penalty:
            kwargs["frequency_penalty"] = float(frequency_penalty)
        if presence_penalty:
            kwargs["presence_penalty"] = float(presence_penalty)
        
        return ChatOpenAI(**kwargs)
        
    elif model.type == "bedrock":
        bedrock_config = config.get("bedrock", {})
        temperature = bedrock_config.get("temperature")
        max_tokens = bedrock_config.get("maxTokens")
        
        # For Bedrock, we'd need to use a different client
        # This is a placeholder - actual Bedrock integration would be different
        raise NotImplementedError("Bedrock support not implemented in LangChain executor")
    
    else:
        raise ValueError(f"Unsupported model type: {model.type}")


def create_embeddings_client(model, embeddings_model_name: Optional[str] = None) -> OpenAIEmbeddings:
    """Create OpenAI embeddings client."""
    model_name = embeddings_model_name or model.name

    # Special case: if embeddings_model_name is an OpenAI model, use Azure OpenAI config
    if embeddings_model_name and embeddings_model_name.startswith("text-embedding"):
        # Use hardcoded Azure OpenAI configuration for embeddings
        # This allows using Azure OpenAI for embeddings while using local Ollama for LLM
        logger.info(f"Using Azure OpenAI configuration for embeddings model: {embeddings_model_name}")

        # Read the secret value from environment variable
        import os
        api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("Azure OpenAI API key not available for embeddings - AZURE_OPENAI_API_KEY environment variable not set")

        base_url = "https://azure.prod.ai-gateway.quantumblack.com/80948656-dd10-4633-be49-4ebd6c302368"
        api_version = "2024-12-01-preview"

        # Handle JWT tokens for enterprise Azure setups
        default_headers = {}
        if api_key.startswith("eyJ"):  # JWT token (starts with eyJ)
            default_headers["api-key"] = api_key
            api_key_param = api_key
        else:
            api_key_param = api_key

        # Azure OpenAI embeddings
        full_base_url = f"{base_url.rstrip('/')}/openai/deployments/{model_name}/"
        kwargs = {
            "model": model_name,
            "api_key": SecretStr(api_key_param),
            "base_url": full_base_url,
            "api_version": api_version,
            "default_query": {"api-version": api_version} if api_version else {},
        }

        # Add custom headers for JWT tokens
        if default_headers:
            kwargs["default_headers"] = default_headers
            kwargs["headers"] = default_headers

        return OpenAIEmbeddings(**kwargs)

    # Use the provided model configuration for everything else
    config = model.config

    if model.type == "azure":
        azure_config = config.get("azure", {})
        api_key = azure_config.get("apiKey", "")
        base_url = azure_config.get("baseUrl", "")
        api_version = azure_config.get("apiVersion", "")
        
        if not api_key or not base_url:
            raise ValueError("Azure OpenAI requires apiKey and baseUrl")
            
        # Handle JWT tokens for enterprise Azure setups
        default_headers = {}
        if api_key.startswith("eyJ"):  # JWT token (starts with eyJ)
            # For JWT tokens, use api-key header like ARK controller
            default_headers["api-key"] = api_key
            # Still set api_key for LangChain compatibility
            api_key_param = api_key
        else:
            # Standard Azure API key
            api_key_param = api_key

        # Azure OpenAI embeddings
        full_base_url = f"{base_url.rstrip('/')}/openai/deployments/{model_name}/"
        kwargs = {
            "model": model_name,
            "api_key": SecretStr(api_key_param),
            "base_url": full_base_url,
            "api_version": api_version,
            "default_query": {"api-version": api_version} if api_version else {},
        }

        # Add custom headers for JWT tokens
        if default_headers:
            kwargs["default_headers"] = default_headers
            # ALSO try the headers parameter for OpenAIEmbeddings compatibility
            kwargs["headers"] = default_headers

        return OpenAIEmbeddings(**kwargs)
        
    elif model.type == "openai":
        openai_config = config.get("openai", {})
        api_key = openai_config.get("apiKey", "")
        base_url = openai_config.get("baseUrl", "")
        
        if not api_key:
            raise ValueError("OpenAI requires apiKey")
            
        return OpenAIEmbeddings(
            model=model_name, 
            api_key=SecretStr(api_key),
            base_url=base_url or None
        )
    
    else:
        raise ValueError(f"Unsupported model type for embeddings: {model.type}")


def should_use_rag(agent_config) -> bool:
    """Check if the agent should use RAG based on labels."""
    logger.info(f"should_use_rag check - hasattr: {hasattr(agent_config, 'labels')}")
    logger.info(f"should_use_rag check - labels: {getattr(agent_config, 'labels', None)}")
    if not hasattr(agent_config, "labels") or not agent_config.labels:
        logger.info("should_use_rag: No labels found, returning False")
        return False
    rag_value = agent_config.labels.get("langchain")
    logger.info(f"should_use_rag: langchain label value = '{rag_value}'")
    result = rag_value == "rag"
    logger.info(f"should_use_rag: returning {result}")
    return result


def index_code_files(code_directory: str = ".") -> List[Document]:
    """Index Python and text files from local code using text splitting."""
    base_path = Path(code_directory)
    logger.info(f"Indexing files from {base_path}")

    # Collect Python and text files from current directory and subdirectories
    files_to_index = []
    for file_pattern in ["*.py", "*.txt", "*.md"]:
        for file_path in base_path.rglob(file_pattern):
            # Skip dependencies and cache directories
            if not any(part in file_path.parts for part in ["__pycache__", ".git", "node_modules", "venv", ".env", "site-packages", ".venv"]):
                files_to_index.append(file_path)

    # Read and process files
    documents = []
    for file_path in files_to_index:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Create document with metadata
            doc = Document(
                page_content=content,
                metadata={
                    "file_path": str(file_path),
                    "file_name": file_path.name,
                    "relative_path": str(file_path.relative_to(code_directory)),
                },
            )
            documents.append(doc)

        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")

    if not documents:
        logger.warning("No files found to index")
        return []

    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\nclass ", "\n\ndef ", "\n\nasync def ", "\n\n", "\n", " "],
    )

    chunks = text_splitter.split_documents(documents)
    logger.info(f"Created {len(chunks)} code chunks from {len(documents)} files")
    
    return chunks


def create_vector_store(chunks: List[Document], embeddings: OpenAIEmbeddings) -> Optional[FAISS]:
    """Create FAISS vector store from document chunks."""
    try:
        vector_store = FAISS.from_documents(chunks, embeddings)
        logger.info(f"Created FAISS vector store with {len(chunks)} chunks")
        return vector_store
    except Exception as e:
        logger.error(f"Failed to create FAISS vector store: {e}")
        return None


def build_rag_context(docs: List[Document]) -> str:
    """Build context string from retrieved documents."""
    if not docs:
        return "No relevant code context found."

    context_parts = []
    for doc in docs:
        file_path = doc.metadata.get("relative_path", "unknown")
        content = doc.page_content
        context_parts.append(f"## File: {file_path}\n```python\n{content}\n```\n")

    return "\n".join(context_parts)