"""Custom middleware for request processing."""

import time
import uuid
from typing import Callable, Optional
from contextvars import ContextVar
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from app.core.logger import logger
from app.core.config import settings
from app.services.auth.utils.session_auth import update_session_activity, set_session_cookie

# Context variables for request-scoped data
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
request_start_time_var: ContextVar[Optional[float]] = ContextVar("request_start_time", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation ID to all requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Store in context variable
        correlation_id_var.set(correlation_id)
        
        # Record request start time
        start_time = time.time()
        request_start_time_var.set(start_time)
        
        # Add correlation ID to response headers
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response


class SessionActivityMiddleware(BaseHTTPMiddleware):
    """Middleware to update session activity on each request."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get session token from cookies
        session_token = request.cookies.get("session_token")
        
        # Process the request
        response = await call_next(request)
        
        # Update session activity if token exists and request was successful
        if session_token and response.status_code < 400:
            try:
                updated_token = update_session_activity(session_token)
                if updated_token:
                    # Set the updated token in the response
                    set_session_cookie(response, updated_token)
            except Exception as e:
                logger.warning(f"Failed to update session activity: {str(e)}")
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log request/response information."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        logger.info(
            f"{request.method} {request.url.path} started",
            extra={
                "request_id": getattr(request.state, 'correlation_id', None),
                "event_type": "api_request",
                "method": request.method,
                "path": request.url.path,
                "user_id": getattr(request.state, 'user_id', None),
                "user_agent": request.headers.get("user-agent"),
                "ip_address": request.client.host if request.client else None,
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000
        
        # Log response
        logger.info(
            f"{request.method} {request.url.path} completed",
            extra={
                "request_id": getattr(request.state, 'correlation_id', None),
                "event_type": "api_response",
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "response_time_ms": response_time,
            }
        )
        
        return response


# Utility functions for backward compatibility
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
