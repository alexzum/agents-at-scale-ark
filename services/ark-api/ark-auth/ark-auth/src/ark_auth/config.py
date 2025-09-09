from pydantic_settings import BaseSettings
from typing import Optional

class AuthSettings(BaseSettings):
    okta_issuer: Optional[str] = None
    okta_audience: Optional[str] = None
    skip_auth: bool = False

    model_config = {
        "env_prefix": "ARK_",
        "env_file": ".env",
        "extra": "ignore"  # Ignore extra environment variables
    }

settings = AuthSettings()
