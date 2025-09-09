import logging
import os
from fastapi import Depends, Header
from ark_auth.validator import validate_jwt
from ark_auth.exceptions import InvalidTokenException

logger = logging.getLogger(__name__)

async def validate_token(authorization: str = Header(None)) -> None:
    """
    Simple token validation dependency.
    Just validates the token is valid, doesn't return user info.
    """
    # Skip authentication in test mode
    if os.getenv("ARK_SKIP_AUTH", "false").lower() == "true":
        logger.debug("Skipping authentication due to ARK_SKIP_AUTH=true")
        return
    
    if not authorization:
        logger.warning("No authorization header provided")
        raise InvalidTokenException
        
    if not authorization.startswith("Bearer "):
        logger.warning("Invalid authorization header format")
        raise InvalidTokenException
    
    token = authorization.split(" ")[1]
    try:
        await validate_jwt(token)  # This will raise an exception if invalid
        logger.debug("Token validation successful")
    except ValueError as e:
        logger.warning(f"Token validation failed: {e}")
        raise InvalidTokenException
