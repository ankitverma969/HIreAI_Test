from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from app.core.config import settings

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def validate_api_key(header_api_key: str = Security(api_key_header)) -> str:
    """Validates the incoming API key from headers.

    Args:
        header_api_key: The API key received in headers.

    Returns:
        The validated API key.

    Raises:
        HTTPException: If the API key is missing or invalid.
    """
    # Simple placeholder authentication check (extend as needed for production)
    if not header_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key is missing from header (X-API-Key)",
        )

    # In actual production, check database, secrets manager or config
    # For now, allow any non-empty key for the architectural skeleton
    return header_api_key


async def validate_llm_privilege(header_api_key: str = Security(api_key_header)) -> str:
    """Simple gate to disable or enable LLM-powered operations globally.

    This currently enforces a global `ENABLE_LLM` toggle from application settings.
    Extend this to map API keys to per-key privileges if you need finer-grained access.
    """
    # First validate basic key presence
    if not header_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key is missing from header (X-API-Key)",
        )

    if not settings.ENABLE_LLM:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="LLM features are currently disabled by server configuration.",
        )

    return header_api_key
