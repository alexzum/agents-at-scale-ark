from fastapi import Depends, Header
from ark_auth.validator import validate_jwt
from ark_auth.exceptions import InvalidTokenException
import os

async def validate_token(authorization: str = Header(None)) -> None:
    """
    Simple token validation dependency.
    Just validates the token is valid, doesn't return user info.
    """
    # Skip authentication in test mode
    if os.getenv("ARK_SKIP_AUTH", "false").lower() == "true":
        return
    
    if not authorization:
        raise InvalidTokenException
        
    if not authorization.startswith("Bearer "):
        raise InvalidTokenException
    token = authorization.split(" ")[1]
    try:
        await validate_jwt(token)  # This will raise an exception if invalid
    except ValueError:
        raise InvalidTokenException
