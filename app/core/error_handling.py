"""Standardized error handling utilities."""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from app.config.error_codes import ErrorCode, get_error_response
from app.core.logger import logger


def handle_database_error(error: Exception, operation: str, resource: str) -> HTTPException:
    """Handle database errors with standardized responses."""
    logger.error(f"Database error in {operation} for {resource}: {str(error)}")
    
    if "duplicate key" in str(error).lower():
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=get_error_response(ErrorCode.TAG_ALREADY_EXISTS)["message"]
        )
    elif "not found" in str(error).lower():
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=get_error_response(ErrorCode.RESOURCE_NOT_FOUND)["message"]
        )
    else:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_response(ErrorCode.INTERNAL_SERVER_ERROR)["message"]
        )


def handle_validation_error(field: str, message: str) -> HTTPException:
    """Handle validation errors with standardized responses."""
    logger.error(f"Validation error for field {field}: {message}")
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Validation error: {field} - {message}"
    )


def handle_permission_error(user_id: str, action: str, resource: str) -> HTTPException:
    """Handle permission errors with standardized responses."""
    logger.warning(f"Permission denied: User {user_id} cannot {action} {resource}")
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=get_error_response(ErrorCode.PERMISSION_DENIED)["message"]
    )


def handle_external_api_error(service: str, error: Exception) -> HTTPException:
    """Handle external API errors with standardized responses."""
    logger.error(f"External API error from {service}: {str(error)}")
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=get_error_response(ErrorCode.EXTERNAL_SERVICE_ERROR)["message"]
    )


async def safe_database_operation(operation_func, *args, **kwargs):
    """Safely execute database operations with error handling."""
    try:
        return await operation_func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Database operation failed: {str(e)}")
        raise handle_database_error(e, "operation", "database")