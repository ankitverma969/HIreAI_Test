from typing import Generator
from fastapi import Depends
from app.core.config import Settings, settings
from app.core.security import validate_api_key

def get_settings() -> Settings:
    """Dependency provider for application configurations."""
    return settings


def get_security_key(api_key: str = Depends(validate_api_key)) -> str:
    """Dependency provider ensuring validated API key header is present."""
    return api_key
