"""Authentication configuration for ARK SDK."""

from pydantic_settings import BaseSettings
from typing import Optional


class AuthConfig(BaseSettings):
    """Configuration for authentication."""
    
    # JWT settings
    jwt_algorithm: str = "RS256"
    jwt_audience: Optional[str] = None
    jwt_issuer: Optional[str] = None
    
    # Key fetching settings
    jwks_url: Optional[str] = None
    jwks_cache_ttl: int = 3600  # 1 hour
    
    # Token validation settings
    token_validation_timeout: int = 30  # seconds
    token_validation_retries: int = 3
    
    class Config:
        env_prefix = "ARK_AUTH_"
        case_sensitive = False
