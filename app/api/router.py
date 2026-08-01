from datetime import datetime
from fastapi import APIRouter
from app.core.config import settings
from app.models.response import SuccessResponse

router = APIRouter()

@router.get("/", response_model=SuccessResponse[dict[str, str]])
async def root() -> SuccessResponse[dict[str, str]]:
    """Root endpoint welcoming users to the screening service."""
    return SuccessResponse(
        message=f"Welcome to the {settings.APP_NAME} Service",
        data={
            "status": "online",
            "documentation": "/docs"
        }
    )


@router.get("/health", response_model=SuccessResponse[dict[str, str]])
async def health() -> SuccessResponse[dict[str, str]]:
    """Health check endpoint checking application viability."""
    return SuccessResponse(
        message="System status healthy",
        data={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@router.get("/version", response_model=SuccessResponse[dict[str, str]])
async def version() -> SuccessResponse[dict[str, str]]:
    """Version check endpoint returning current release metadata."""
    return SuccessResponse(
        message="Version check succeeded",
        data={
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION
        }
    )
