"""Minimal A2A Server - The absolute minimum required to get an A2A server working."""

import asyncio
import uuid
from typing import Any

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill, Message, Part, Role, TextPart
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse


class MinimalExecutor:
    """Minimal executor that just echoes back the message."""
    
    async def execute(self, context, event_queue):
        """Execute a task and send response back."""
        # Extract message text
        message_text = ""
        if context.message and context.message.parts:
            first_part = context.message.parts[0]
            if hasattr(first_part, "root") and hasattr(first_part.root, "text"):
                message_text = first_part.root.text
        
        # Simple response
        response = f"Echo: {message_text}"
        
        # Send response back
        response_message = Message(
            messageId=str(uuid.uuid4()),
            contextId=context.message.context_id if context.message else str(uuid.uuid4()),
            taskId=context.task_id,
            role=Role.agent,
            parts=[Part(root=TextPart(kind="text", text=response))],
        )
        await event_queue.enqueue_event(response_message)
    
    async def cancel(self, context, event_queue):
        """Cancel a running task."""
        pass


def create_app():
    """Create the minimal A2A application."""
    
    # Minimal agent card
    agent_card = AgentCard(
        name="minimal-agent",
        description="Minimal A2A agent",
        url="http://localhost:8000/",
        version="1.0.0",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[
            AgentSkill(
                id="echo",
                name="Echo",
                description="Echo back messages",
                tags=["echo"],
                examples=["Hello world"],
                inputModes=["text/plain"],
                outputModes=["text/plain"],
            )
        ],
    )
    
    # Create handler
    handler = DefaultRequestHandler(
        agent_executor=MinimalExecutor(),
        task_store=InMemoryTaskStore(),
    )
    
    # Create A2A app
    a2a_app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=handler,
    )
    
    # Health check
    async def health(request):
        return JSONResponse({"status": "ok"})
    
    # Build app
    built_a2a_app = a2a_app.build()
    routes = [Route("/health", health, methods=["GET"])]
    
    # Add A2A routes
    for route in built_a2a_app.routes:
        if hasattr(route, 'path'):
            if route.path == "/":
                routes.append(Route("/", route.endpoint, methods=route.methods))
            elif route.path == "/.well-known/agent.json":
                routes.append(route)
    
    return Starlette(routes=routes)


def main():
    """Main entry point."""
    app = create_app()
    print("Starting minimal A2A server on http://localhost:8000")
    print("Health check: http://localhost:8000/health")
    print("Agent card: http://localhost:8000/.well-known/agent.json")
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
