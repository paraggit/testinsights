"""Custom exceptions and error handlers for the API."""

import structlog
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = structlog.get_logger(__name__)


class TestInsightException(Exception):
    """Base exception for TestInsight API."""

    def __init__(self, message: str, error_type: str = "TestInsightError"):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)


class LLMProviderException(TestInsightException):
    """Exception for LLM provider errors."""

    def __init__(self, message: str):
        super().__init__(message, "LLMProviderError")


class StorageException(TestInsightException):
    """Exception for storage-related errors."""

    def __init__(self, message: str):
        super().__init__(message, "StorageError")


class SyncException(TestInsightException):
    """Exception for synchronization errors."""

    def __init__(self, message: str):
        super().__init__(message, "SyncError")


class ConfigurationException(TestInsightException):
    """Exception for configuration errors."""

    def __init__(self, message: str):
        super().__init__(message, "ConfigurationError")


async def test_insight_exception_handler(
    request: Request, exc: TestInsightException
):  # type: ignore
    """Handle TestInsight custom exceptions."""
    logger.error(f"{exc.error_type}: {exc.message}")

    return JSONResponse(
        status_code=500,
        content={"error": exc.message, "error_type": exc.error_type, "detail": None},
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "error_type": "HTTPError", "detail": None},
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.exception("Unhandled exception occurred")

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_type": "InternalError",
            "detail": str(exc) if logger.level == "DEBUG" else None,
        },
    )
