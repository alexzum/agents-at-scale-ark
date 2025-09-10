"""FastAPI dependencies for authentication."""

import logging
from fastapi import Depends, HTTPException, Header
from typing import Optional

from .validator import TokenValidator
from .config import AuthConfig
from .exceptions import create_auth_exception

logger = logging.getLogger(__name__)

# Global validator instance
_validator: Optional[TokenValidator] = None


def get_validator() -> TokenValidator:
    """Get the global token validator instance."""
    global _validator
    if _validator is None:
        _validator = TokenValidator(AuthConfig())
    return _validator


async def validate_token(authorization: str = Header(..., alias="Authorization")) -> dict:
    """
    FastAPI dependency to validate JWT tokens.
    
    Args:
        authorization: The Authorization header value
        
    Returns:
        The decoded token payload
        
    Raises:
        HTTPException: If token validation fails
    """
    if not authorization.startswith("Bearer "):
        raise create_auth_exception("Invalid authorization header format")
    
    token = authorization[7:]  # Remove "Bearer " prefix
    
    if not token:
        raise create_auth_exception("Missing token")
    
    try:
        validator = get_validator()
        payload = await validator.validate_token_with_retry(token)
        return payload
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        raise create_auth_exception("Token validation failed")


def get_current_user(token_payload: dict = Depends(validate_token)) -> dict:
    """
    FastAPI dependency to get the current user from token payload.
    
    Args:
        token_payload: The validated token payload
        
    Returns:
        The user information from the token
    """
    return {
        "sub": token_payload.get("sub"),
        "email": token_payload.get("email"),
        "name": token_payload.get("name"),
        "roles": token_payload.get("roles", []),
        "permissions": token_payload.get("permissions", []),
    }
