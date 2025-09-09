"""Test-specific app factory without authentication middleware."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from kubernetes_asyncio import client

from .api import router
from .core.config import setup_logging
from ark_sdk.k8s import init_k8s

# Initialize logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up ARK API (TEST MODE)...")
    await init_k8s()
    logger.info("Kubernetes clients initialized")
    yield
    # Shutdown
    logger.info("Shutting down ARK API...")
    # Close all kubernetes async clients
    await client.ApiClient().close()


def create_test_app() -> FastAPI:
    """Create a FastAPI app for testing without authentication middleware."""
    
    app = FastAPI(
        title="ARK API (Test Mode)",
        description="Agentic Runtime for Kubenetes API - Test Version",
        version="1.0.0",
        lifespan=lifespan,
        root_path_in_servers=True,
        openapi_url=None,
        docs_url=None
    )

    # Custom docs endpoint
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html(request: Request):
        forwarded_prefix = request.headers.get("x-forwarded-prefix", "")
        openapi_url = f"{forwarded_prefix}/openapi.json"
        
        return get_swagger_ui_html(
            openapi_url=openapi_url,
            title=app.title + " - Swagger UI",
        )

    # Custom OpenAPI spec
    @app.get("/openapi.json", include_in_schema=False)
    async def custom_openapi(request: Request):
        openapi_schema = app.openapi()
        
        forwarded_prefix = request.headers.get("x-forwarded-prefix", "")
        
        if forwarded_prefix:
            host = request.headers.get("x-forwarded-host") or request.headers.get("host", "localhost:8000")
            protocol = request.headers.get("x-forwarded-proto", "http")
            server_url = f"{protocol}://{host}{forwarded_prefix}"
            
            openapi_schema["servers"] = [{"url": server_url, "description": "Current server"}]
        
        return openapi_schema

    # Configure CORS
    cors_origins = os.getenv("CORS_ORIGINS", "").strip()
    allowed_origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()] if cors_origins else []

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routes
    app.include_router(router)

    # NOTE: No authentication middleware added for tests!

    # Custom exception handler for validation errors
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors with detailed logging."""
        logger.error(f"Validation error for {request.method} {request.url}")
        logger.error(f"Request body: {await request.body()}")
        logger.error(f"Validation errors: {exc.errors()}")
        
        return JSONResponse(
            status_code=422,
            content={
                "detail": exc.errors(),
                "body": exc.body
            }
        )
    
    return app
