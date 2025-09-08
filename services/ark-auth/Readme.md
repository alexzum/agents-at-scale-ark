# ARK Auth

Authentication utilities for ARK services. Provides JWT token validation using Okta as the identity provider.

## Features

- JWT token validation using `pyjwt` and `pyjwt-key-fetcher`
- Okta integration for token verification
- FastAPI dependency injection for easy integration
- Simple token validation without user context extraction
- Configurable issuer and audience validation

## Installation

```bash
# Install from local source
pip install -e .

# Or add to your pyproject.toml
ark-auth = { path = "../../ark-auth/ark-auth/", develop = true }
```

## Configuration

Set the following environment variables:

```bash
export ARK_OKTA_ISSUER="https://your-okta-domain.okta.com/oauth2/default"
export ARK_OKTA_AUDIENCE="your-api-audience"
```

Or create a `.env` file:

```env
ARK_OKTA_ISSUER=https://your-okta-domain.okta.com/oauth2/default
ARK_OKTA_AUDIENCE=your-api-audience
```

## Usage

### Basic Token Validation

```python
from ark_auth.validator import validate_jwt

# Validate a JWT token
try:
    payload = await validate_jwt("your-jwt-token")
    print("Token is valid!")
except ValueError as e:
    print(f"Token validation failed: {e}")
```

### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from ark_auth.dependencies import validate_token

app = FastAPI()

@app.get("/protected")
async def protected_route(_: None = Depends(validate_token)):
    return {"message": "This route is protected"}

@app.get("/public")
async def public_route():
    return {"message": "This route is public"}
```

### Advanced Usage

```python
from ark_auth.config import settings
from ark_auth.exceptions import InvalidTokenException

# Access configuration
print(f"Issuer: {settings.okta_issuer}")
print(f"Audience: {settings.okta_audience}")

# Handle authentication errors
try:
    await validate_token("invalid-token")
except InvalidTokenException:
    print("Invalid or expired token")
```

## API Reference

### Functions

#### `validate_jwt(token: str) -> dict`

Validates a JWT token and returns the payload.

**Parameters:**
- `token` (str): The JWT token to validate

**Returns:**
- `dict`: The decoded JWT payload

**Raises:**
- `ValueError`: If token validation fails

#### `validate_token(authorization: str) -> None`

FastAPI dependency for token validation. Validates the Authorization header.

**Parameters:**
- `authorization` (str): The Authorization header value

**Raises:**
- `InvalidTokenException`: If the token is invalid or missing

### Configuration

#### `AuthSettings`

Pydantic settings class for configuration.

**Fields:**
- `okta_issuer` (str): Okta issuer URL
- `okta_audience` (str): Expected audience for tokens

**Environment Variables:**
- `ARK_OKTA_ISSUER`: Okta issuer URL
- `ARK_OKTA_AUDIENCE`: Expected audience

### Exceptions

#### `InvalidTokenException`

HTTP exception raised when token validation fails.

**Status Code:** 401 Unauthorized  
**Headers:** `WWW-Authenticate: Bearer`

## Integration with ARK API

This package is designed to work seamlessly with ARK API services. See the main ARK API documentation for complete integration examples.

### Adding Authentication to Routes

```python
from fastapi import APIRouter, Depends
from ark_auth.dependencies import validate_token

router = APIRouter()

@router.get("/my-endpoint")
async def my_endpoint(_: None = Depends(validate_token)):
    return {"data": "protected data"}
```

### Checking Authentication Status

Use the provided utilities to inspect which routes have authentication:

```bash
# Show all authenticated routes
python3 show_auth_routes_simple.py

# Show only authenticated routes
python3 show_auth_routes_simple.py auth

# Show only public routes
python3 show_auth_routes_simple.py public
```

## Dependencies

- `fastapi>=0.115.0` - Web framework
- `httpx>=0.24.0` - HTTP client
- `pyjwt>=2.10.0` - JWT handling
- `pyjwt-key-fetcher>=0.3.0` - Key fetching for JWT validation
- `pydantic>=2.0.0` - Data validation
- `pydantic-settings>=2.0.0` - Settings management

## Development

### Project Structure

```
ark-auth/
├── src/
│   └── ark_auth/
│       ├── __init__.py          # Package exports
│       ├── config.py            # Configuration settings
│       ├── dependencies.py      # FastAPI dependencies
│       ├── exceptions.py        # Custom exceptions
│       ├── utils.py            # Utility functions
│       └── validator.py        # JWT validation logic
├── pyproject.toml              # Project configuration
└── README.md                   # This file
```

### Building

```bash
# Build the package
python -m build

# Install in development mode
pip install -e .
```

## Security Considerations

- Always use HTTPS in production
- Keep your Okta configuration secure
- Regularly rotate your JWT signing keys
- Monitor for invalid token attempts
- Consider implementing rate limiting for authentication endpoints

## Troubleshooting

### Common Issues

1. **ImportError: No module named 'ark_auth'**
   - Ensure the package is installed: `pip install -e .`
   - Check your Python path includes the source directory

2. **Token validation fails**
   - Verify your Okta issuer and audience configuration
   - Check that the token is not expired
   - Ensure the token format is correct (Bearer token)

3. **Configuration not loading**
   - Set environment variables: `export ARK_OKTA_ISSUER=...`
   - Or create a `.env` file with the required variables

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## License

This project is part of the ARK (Agentic Runtime for Kubernetes) project. See the main project LICENSE file for details.
