"""Shared types for execution engine services."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class Parameter(BaseModel):
    """Parameter for agent configuration."""
    name: str
    value: str


class Model(BaseModel):
    """Model configuration for LLM providers."""
    name: str
    type: str
    config: Dict[str, Any] = {}


class AgentConfig(BaseModel):
    """Agent configuration."""
    name: str
    namespace: str
    prompt: str
    description: str = ""
    parameters: List[Parameter] = []
    model: Model
    labels: Dict[str, str] = {}


class ToolDefinition(BaseModel):
    """Tool definition for agent capabilities."""
    name: str
    description: str
    parameters: Dict[str, Any] = {}


class Message(BaseModel):
    """Message in conversation history."""
    role: str
    content: str
    name: str = ""

    class Config:
        extra = "allow"


class ExecutionEngineRequest(BaseModel):
    """Request to execute an agent."""
    agent: AgentConfig
    userInput: Message
    history: List[Message]
    tools: List[ToolDefinition] = []


class TokenUsage(BaseModel):
    """Token usage information from LLM calls."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ExecutionEngineResponse(BaseModel):
    """Response from agent execution."""
    messages: List[Message]
    error: str = ""
    token_usage: Optional[TokenUsage] = None