"""Token validation for ARK SDK."""

import asyncio
import logging
from typing import Optional, Dict, Any
import httpx
from pyjwt import decode, PyJWKClient
from pyjwt.exceptions import InvalidTokenError, ExpiredSignatureError, DecodeError

from .exceptions import TokenValidationError, InvalidTokenError as AuthInvalidTokenError, ExpiredTokenError
from .config import AuthConfig

logger = logging.getLogger(__name__)


class TokenValidator:
    """Validates JWT tokens using JWKS."""
    
    def __init__(self, config: Optional[AuthConfig] = None):
        self.config = config or AuthConfig()
        self._jwks_client: Optional[PyJWKClient] = None
        self._jwks_cache: Dict[str, Any] = {}
        self._cache_expiry: Optional[float] = None
    
    def _get_jwks_client(self) -> PyJWKClient:
        """Get or create JWKS client."""
        if self._jwks_client is None and self.config.jwks_url:
            self._jwks_client = PyJWKClient(
                self.config.jwks_url,
                cache_ttl=self.config.jwks_cache_ttl
            )
        return self._jwks_client
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a JWT token.
        
        Args:
            token: The JWT token to validate
            
        Returns:
            The decoded token payload
            
        Raises:
            TokenValidationError: If token validation fails
        """
        try:
            # Get the JWKS client
            jwks_client = self._get_jwks_client()
            if jwks_client is None:
                raise TokenValidationError("JWKS URL not configured")
            
            # Get the signing key
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            
            # Use OKTA values as fallback if JWT values are not set
            audience = self.config.jwt_audience or self.config.okta_audience
            issuer = self.config.jwt_issuer or self.config.okta_issuer
            
            # Decode and validate the token
            payload = decode(
                token,
                signing_key.key,
                algorithms=[self.config.jwt_algorithm],
                audience=audience,
                issuer=issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": audience is not None,
                    "verify_iss": issuer is not None,
                }
            )
            
            return payload
            
        except ExpiredSignatureError as e:
            logger.warning(f"Token expired: {e}")
            raise ExpiredTokenError("Token has expired")
        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise AuthInvalidTokenError("Invalid token")
        except DecodeError as e:
            logger.warning(f"Token decode error: {e}")
            raise AuthInvalidTokenError("Token could not be decoded")
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise TokenValidationError(f"Token validation failed: {e}")
    
    async def validate_token_with_retry(self, token: str) -> Dict[str, Any]:
        """
        Validate a JWT token with retry logic.
        
        Args:
            token: The JWT token to validate
            
        Returns:
            The decoded token payload
            
        Raises:
            TokenValidationError: If token validation fails after retries
        """
        last_error = None
        
        for attempt in range(self.config.token_validation_retries):
            try:
                return await self.validate_token(token)
            except TokenValidationError as e:
                last_error = e
                if attempt < self.config.token_validation_retries - 1:
                    logger.warning(f"Token validation attempt {attempt + 1} failed, retrying: {e}")
                    await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"Token validation failed after {self.config.token_validation_retries} attempts")
        
        raise last_error or TokenValidationError("Token validation failed after retries")
