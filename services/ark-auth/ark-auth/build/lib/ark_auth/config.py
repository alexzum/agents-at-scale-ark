from pydantic_settings import BaseSettings
from typing import Optional

class AuthSettings(BaseSettings):
    okta_issuer: Optional[str] = None
    okta_audience: Optional[str] = None

    model_config = {
        "env_prefix": "ARK_",
        "env_file": ".env"
    }

settings = AuthSettings()
