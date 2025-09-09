# ARK Auth Package

Authentication utilities for ARK services.

## Features

- JWT token validation using Okta
- FastAPI dependency injection for authentication
- Configurable authentication settings
- Support for skipping authentication in test environments

## Installation

```bash
pip install -e .
```

## Usage

```python
from ark_auth import validate_token
from fastapi import Depends

@app.get("/protected")
async def protected_route(token: None = Depends(validate_token)):
    return {"message": "This is a protected route"}
```

## Configuration

Set the following environment variables:

- `ARK_OKTA_ISSUER`: Okta issuer URL
- `ARK_OKTA_AUDIENCE`: Okta audience
- `ARK_SKIP_AUTH`: Set to "true" to skip authentication (for testing)
