import os
from .config import ArkAuthSettings

def load_settings() -> ArkAuthSettings:
    return ArkAuthSettings()
