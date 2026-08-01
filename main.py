import time
from typing import Awaitable, Callable
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.api.router import router as api_router
from app.core.config import settings
from app.core.exceptions import (
    ExportException,
    LLMException,
    ParsingException,
    ResumeAgentException,
    ScoringException,
    ValidationException,
)
from app.core.logging import setup_logging


def create_app() -> FastAPI:
    """Application factory for the Resume Screening Agent FastAPI backend.

    Returns:
        Configured FastAPI application instance.
    """
    # 1. Initialize logging
    setup_logging()
    logger.info("Initializing FastAPI Application...")

    # 2. Instantiate FastAPI
    app = FastAPI(
        title=settings.APP_NAME,
        description="Clean-architecture enterprise-grade AI Resume Screening service",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 3. Add CORS Middleware configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Adjust for production scoping
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 4. Add Global Request/Response Logging Middleware
    @app.middleware("http")
    async def log_requests(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start_time = time.perf_counter()
        logger.debug(f"Received request: {request.method} {request.url.path}")

        try:
            response = await call_next(request)
            process_time = time.perf_counter() - start_time
            logger.info(
                f"Request complete: {request.method} {request.url.path} "
                f"| Status: {response.status_code} | Time: {process_time:.4f}s"
            )
            return response
        except Exception as e:
            process_time = time.perf_counter() - start_time
            logger.exception(
                f"Unhandled exception during: {request.method} {request.url.path} "
                f"| Time: {process_time:.4f}s | Error: {str(e)}"
            )
            raise e

    # 5. Register Custom Exception Handlers mapping domain exceptions to HTTP Status codes
    @app.exception_handler(ResumeAgentException)
    async def resume_agent_exception_handler(
        request: Request, exc: ResumeAgentException
    ) -> JSONResponse:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        if isinstance(exc, ValidationException):
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        elif isinstance(exc, ParsingException):
            status_code = status.HTTP_400_BAD_REQUEST
        elif isinstance(exc, LLMException):
            status_code = status.HTTP_502_BAD_GATEWAY
        elif isinstance(exc, ScoringException):
            status_code = status.HTTP_400_BAD_REQUEST
        elif isinstance(exc, ExportException):
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        logger.warning(f"Domain Exception: {exc.__class__.__name__} - {exc.message}")
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "error_code": exc.__class__.__name__,
                "detail": exc.message,
            },
        )

    # 6. Include Router endpoints
    app.include_router(api_router)

    logger.info("Application startup check complete.")
    return app


app = create_app()
