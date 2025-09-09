import os
from .config import AuthSettings

def load_settings() -> AuthSettings:
    return AuthSettings()
