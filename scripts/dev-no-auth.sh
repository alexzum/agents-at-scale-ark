#!/bin/bash
# Development script with authentication disabled

echo "Starting ARK API with authentication DISABLED"
echo "This is for development/testing only!"
echo ""

cd services/ark-api/ark-api
ARK_SKIP_AUTH=true CORS_ORIGINS=http://localhost:3000 uv run python -m uvicorn --host 0.0.0.0 --port 8000 --reload src.ark_api.main:app
