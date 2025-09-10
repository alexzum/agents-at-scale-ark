# ARK API

FastAPI-based REST interface for managing ARK Kubernetes resources.

## Quickstart
```bash
make help               # Show available commands
make ark-api-install    # Setup dependencies
make ark-api-dev        # Run in development mode
```

## Environment Variables

The API supports several environment variables for configuration:

### Authentication
- `ARK_SKIP_AUTH`: Set to `"true"` to completely disable authentication for all routes
  - **WARNING**: Only use this in development or testing environments
  - **Default**: `"false"`

### CORS
- `CORS_ORIGINS`: Comma-separated list of allowed origins for CORS
  - **Example**: `http://localhost:3000,https://yourdomain.com`
  - **Default**: Empty (blocks all cross-origin requests)

### Logging
- `LOG_LEVEL`: Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - **Default**: `INFO`

## Configuration

Create a `.env` file in the `services/ark-api/` directory and add your environment variables:
```bash
# Create .env file in services/ark-api/
cat > services/ark-api/.env << EOF
ARK_SKIP_AUTH=false
CORS_ORIGINS=
LOG_LEVEL=INFO
EOF
```

Or copy from the example file:
```bash
cp services/ark-api/.env.example services/ark-api/.env
```

## Notes
- Requires Python 3.11+ and uv package manager
- Run commands from repository root directory
- Provides bridge between client apps and Kubernetes API