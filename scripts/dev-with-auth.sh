#!/bin/bash
# Development script with authentication enabled

echo "Starting ARK API with authentication ENABLED"
echo "To disable authentication, set ARK_SKIP_AUTH=true"
echo ""

cd services/ark-api/ark-api
CORS_ORIGINS=http://localhost:3000 uv run python -m uvicorn --host 0.0.0.0 --port 8000 --reload src.ark_api.main:app
