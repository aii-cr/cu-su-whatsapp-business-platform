"""
Middleware for WhatsApp Business Platform.
Handles correlation ID propagation, request context, and audit logging support.
"""

import time
import uuid
from contextvars import ContextVar
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logger import logger

# Context variables for request-scoped data
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
request_start_time_var: ContextVar[Optional[float]] = ContextVar("request_start_time", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle correlation ID propagation.

    Extracts correlation ID from headers or generates a new one,
    and makes it available throughout the request lifecycle.
    """

    def __init__(self, app: FastAPI):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with correlation ID handling."""

        # Extract or generate correlation ID
        correlation_id = (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("x-correlation-id")
            or str(uuid.uuid4())
        )

        # Store in context variable
        correlation_id_var.set(correlation_id)

        # Record request start time
        start_time = time.time()
        request_start_time_var.set(start_time)

        # Process request
        try:
            response = await call_next(request)

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            # Calculate request duration
            duration = time.time() - start_time

            # Log request completion
            logger.info(
                f"{request.method} {request.url.path} completed",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                    "user_agent": request.headers.get("user-agent"),
                    "client_ip": request.client.host if request.client else None,
                },
            )

            return response

        except Exception as e:
            # Calculate request duration for error case
            duration = time.time() - start_time

            # Log request error
            logger.error(
                f"{request.method} {request.url.path} failed",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "duration_ms": round(duration * 1000, 2),
                    "user_agent": request.headers.get("user-agent"),
                    "client_ip": request.client.host if request.client else None,
                },
                exc_info=True,
            )

            # Re-raise the exception
            raise


class UserContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to capture user context for audit logging.

    Extracts user information from authenticated requests
    and makes it available for audit logging.
    """

    def __init__(self, app: FastAPI):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with user context handling."""

        # Extract user ID from request state (set by authentication middleware)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            user_id_var.set(str(user_id))

        # Process request
        response = await call_next(request)

        return response


def get_correlation_id() -> Optional[str]:
    """
    Get the current correlation ID from context.

    Returns:
        Current correlation ID or None if not set
    """
    return correlation_id_var.get()


def get_request_start_time() -> Optional[float]:
    """
    Get the current request start time from context.

    Returns:
        Request start time or None if not set
    """
    return request_start_time_var.get()


def get_user_id() -> Optional[str]:
    """
    Get the current user ID from context.

    Returns:
        Current user ID or None if not set
    """
    return user_id_var.get()


def get_request_duration() -> Optional[float]:
    """
    Calculate the current request duration in milliseconds.

    Returns:
        Request duration in milliseconds or None if start time not set
    """
    start_time = get_request_start_time()
    if start_time:
        return round((time.time() - start_time) * 1000, 2)
    return None


def setup_middleware(app: FastAPI) -> None:
    """
    Setup all middleware for the application.

    Args:
        app: FastAPI application instance
    """
    # Add correlation ID middleware first
    app.add_middleware(CorrelationIdMiddleware)

    # Add user context middleware
    app.add_middleware(UserContextMiddleware)

    logger.info("Middleware setup completed")
