from fastapi import Depends, Header
from ark_auth.validator import validate_jwt
from ark_auth.exceptions import InvalidTokenException
import os

async def validate_token(authorization: str = Header(None)) -> None:
    """
    Simple token validation dependency.
    Just validates the token is valid, doesn't return user info.
    """
    print(f"DEBUG: validate_token called with authorization: {authorization}")
    
    # Skip authentication in test mode
    if os.getenv("ARK_SKIP_AUTH", "false").lower() == "true":
        print("DEBUG: Skipping auth due to ARK_SKIP_AUTH=true")
        return
    
    if not authorization:
        print("DEBUG: No authorization header, raising InvalidTokenException")
        raise InvalidTokenException
        
    if not authorization.startswith("Bearer "):
        print("DEBUG: Invalid authorization format, raising InvalidTokenException")
        raise InvalidTokenException
    token = authorization.split(" ")[1]
    try:
        print(f"DEBUG: Validating token: {token[:10]}...")
        await validate_jwt(token)  # This will raise an exception if invalid
        print("DEBUG: Token validation successful")
    except ValueError as e:
        print(f"DEBUG: Token validation failed: {e}")
        raise InvalidTokenException
