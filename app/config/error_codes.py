"""
Centralized error codes and user-friendly messages for the WhatsApp Business Platform.
All HTTP exceptions should reference these codes for consistency.
"""

from enum import Enum
from typing import Dict, Any

class ErrorCode(str, Enum):
    """
    Standardized error codes for the application.
    """
    # Authentication & Authorization Errors (1000-1099)
    AUTH_INVALID_CREDENTIALS = "AUTH_1001"
    AUTH_TOKEN_EXPIRED = "AUTH_1002"
    AUTH_TOKEN_INVALID = "AUTH_1003"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_1004"
    AUTH_USER_NOT_FOUND = "AUTH_1005"
    AUTH_USER_INACTIVE = "AUTH_1006"
    AUTH_PASSWORD_WEAK = "AUTH_1007"
    AUTH_EMAIL_ALREADY_EXISTS = "AUTH_1008"
    AUTH_LOGIN_REQUIRED = "AUTH_1009"
    
    # User Management Errors (1100-1199)
    USER_NOT_FOUND = "USER_1101"
    USER_ALREADY_EXISTS = "USER_1102"
    USER_INVALID_DATA = "USER_1103"
    USER_ROLE_NOT_ASSIGNED = "USER_1104"
    USER_DEPARTMENT_NOT_FOUND = "USER_1105"
    USER_PERMISSION_DENIED = "USER_1106"
    
    # Role & Permission Errors (1200-1299)
    ROLE_NOT_FOUND = "ROLE_1201"
    ROLE_ALREADY_EXISTS = "ROLE_1202"
    ROLE_IN_USE = "ROLE_1203"
    PERMISSION_NOT_FOUND = "PERM_1204"
    PERMISSION_ALREADY_EXISTS = "PERM_1205"
    PERMISSION_INVALID = "PERM_1206"
    
    # Department Errors (1300-1399)
    DEPARTMENT_NOT_FOUND = "DEPT_1301"
    DEPARTMENT_ALREADY_EXISTS = "DEPT_1302"
    DEPARTMENT_IN_USE = "DEPT_1303"
    DEPARTMENT_INVALID_DATA = "DEPT_1304"
    
    # WhatsApp Business API Errors (2000-2099)
    WHATSAPP_INVALID_TOKEN = "WA_2001"
    WHATSAPP_WEBHOOK_VERIFICATION_FAILED = "WA_2002"
    WHATSAPP_MESSAGE_SEND_FAILED = "WA_2003"
    WHATSAPP_MEDIA_UPLOAD_FAILED = "WA_2004"
    WHATSAPP_INVALID_PHONE_NUMBER = "WA_2005"
    WHATSAPP_RATE_LIMIT_EXCEEDED = "WA_2006"
    WHATSAPP_API_ERROR = "WA_2007"
    WHATSAPP_TEMPLATE_NOT_APPROVED = "WA_2008"
    WHATSAPP_CONVERSATION_EXPIRED = "WA_2009"
    
    # Conversation & Message Errors (2100-2199)
    CONVERSATION_NOT_FOUND = "CONV_2101"
    CONVERSATION_ALREADY_CLOSED = "CONV_2102"
    CONVERSATION_TRANSFER_FAILED = "CONV_2103"
    CONVERSATION_INVALID_STATUS = "CONV_2104"
    CONVERSATION_ALREADY_ACTIVE = "CONV_2105"
    CONVERSATION_ACCESS_DENIED = "CONV_2106"
    INVALID_CONVERSATION_ID = "CONV_2107"
    MESSAGE_NOT_FOUND = "MSG_2105"
    MESSAGE_SEND_FAILED = "MSG_2106"
    MESSAGE_INVALID_TYPE = "MSG_2107"
    MESSAGE_TOO_LARGE = "MSG_2108"
    MESSAGE_INVALID_CONTENT = "MSG_2109"
    
    # Media & File Errors (2200-2299)
    MEDIA_NOT_FOUND = "MEDIA_2201"
    MEDIA_UPLOAD_FAILED = "MEDIA_2202"
    MEDIA_INVALID_TYPE = "MEDIA_2203"
    MEDIA_TOO_LARGE = "MEDIA_2204"
    MEDIA_DOWNLOAD_FAILED = "MEDIA_2205"
    MEDIA_CORRUPTED = "MEDIA_2206"
    MEDIA_PROCESSING_FAILED = "MEDIA_2207"
    
    # Tag & Label Errors (2300-2399)
    TAG_NOT_FOUND = "TAG_2301"
    TAG_ALREADY_EXISTS = "TAG_2302"
    TAG_INVALID_DATA = "TAG_2303"
    TAG_ASSIGNMENT_FAILED = "TAG_2304"
    
    # Note Errors (2400-2499)
    NOTE_NOT_FOUND = "NOTE_2401"
    NOTE_INVALID_DATA = "NOTE_2402"
    NOTE_CREATE_FAILED = "NOTE_2403"
    NOTE_DELETE_FAILED = "NOTE_2404"
    
    # Database Errors (3000-3099)
    DATABASE_CONNECTION_ERROR = "DB_3001"
    DATABASE_OPERATION_FAILED = "DB_3002"
    DATABASE_CONSTRAINT_VIOLATION = "DB_3003"
    DATABASE_TIMEOUT = "DB_3004"
    DATABASE_MIGRATION_FAILED = "DB_3005"
    
    # Validation Errors (4000-4099)
    VALIDATION_ERROR = "VAL_4001"
    VALIDATION_REQUIRED_FIELD = "VAL_4002"
    VALIDATION_INVALID_FORMAT = "VAL_4003"
    VALIDATION_VALUE_TOO_LONG = "VAL_4004"
    VALIDATION_VALUE_TOO_SHORT = "VAL_4005"
    VALIDATION_INVALID_EMAIL = "VAL_4006"
    VALIDATION_INVALID_PHONE = "VAL_4007"
    VALIDATION_INVALID_DATE = "VAL_4008"
    
    # Rate Limiting Errors (5000-5099)
    RATE_LIMIT_EXCEEDED = "RATE_5001"
    RATE_LIMIT_QUOTA_EXCEEDED = "RATE_5002"
    
    # System Errors (9000-9999)
    INTERNAL_SERVER_ERROR = "SYS_9001"
    SERVICE_UNAVAILABLE = "SYS_9002"
    EXTERNAL_SERVICE_ERROR = "SYS_9003"
    CONFIGURATION_ERROR = "SYS_9004"
    FEATURE_NOT_IMPLEMENTED = "SYS_9005"
    MAINTENANCE_MODE = "SYS_9006"


# Error messages mapping
ERROR_MESSAGES: Dict[ErrorCode, Dict[str, Any]] = {
    # Authentication & Authorization
    ErrorCode.AUTH_INVALID_CREDENTIALS: {
        "message": "Invalid email or password provided",
        "status_code": 401,
        "detail": "Please check your credentials and try again"
    },
    ErrorCode.AUTH_TOKEN_EXPIRED: {
        "message": "Authentication token has expired",
        "status_code": 401,
        "detail": "Please log in again to get a new token"
    },
    ErrorCode.AUTH_TOKEN_INVALID: {
        "message": "Invalid authentication token",
        "status_code": 401,
        "detail": "The provided token is malformed or invalid"
    },
    ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS: {
        "message": "Insufficient permissions to perform this action",
        "status_code": 403,
        "detail": "Contact your administrator for access"
    },
    ErrorCode.AUTH_USER_NOT_FOUND: {
        "message": "User account not found",
        "status_code": 404,
        "detail": "The user account does not exist"
    },
    ErrorCode.AUTH_USER_INACTIVE: {
        "message": "User account is inactive",
        "status_code": 403,
        "detail": "Contact your administrator to activate your account"
    },
    
    # User Management
    ErrorCode.USER_NOT_FOUND: {
        "message": "User not found",
        "status_code": 404,
        "detail": "The requested user does not exist"
    },
    ErrorCode.USER_ALREADY_EXISTS: {
        "message": "User already exists",
        "status_code": 409,
        "detail": "A user with this email already exists"
    },
    
    # Department Management
    ErrorCode.DEPARTMENT_NOT_FOUND: {
        "message": "Department not found",
        "status_code": 404,
        "detail": "The requested department does not exist"
    },
    ErrorCode.DEPARTMENT_ALREADY_EXISTS: {
        "message": "Department already exists",
        "status_code": 409,
        "detail": "A department with this name already exists"
    },
    ErrorCode.DEPARTMENT_IN_USE: {
        "message": "Department is in use",
        "status_code": 400,
        "detail": "Cannot delete department that has assigned users or conversations"
    },
    ErrorCode.DEPARTMENT_INVALID_DATA: {
        "message": "Invalid department data",
        "status_code": 422,
        "detail": "The provided department data is invalid"
    },
    
    # WhatsApp Business API
    ErrorCode.WHATSAPP_INVALID_TOKEN: {
        "message": "Invalid WhatsApp access token",
        "status_code": 401,
        "detail": "Please check your WhatsApp Business API configuration"
    },
    ErrorCode.WHATSAPP_WEBHOOK_VERIFICATION_FAILED: {
        "message": "WhatsApp webhook verification failed",
        "status_code": 403,
        "detail": "Invalid verification token provided"
    },
    ErrorCode.WHATSAPP_MESSAGE_SEND_FAILED: {
        "message": "Failed to send WhatsApp message",
        "status_code": 500,
        "detail": "Unable to deliver message via WhatsApp Business API"
    },
    ErrorCode.WHATSAPP_RATE_LIMIT_EXCEEDED: {
        "message": "WhatsApp API rate limit exceeded",
        "status_code": 429,
        "detail": "Please wait before sending more messages"
    },
    
    # Conversation & Messages
    ErrorCode.CONVERSATION_NOT_FOUND: {
        "message": "Conversation not found",
        "status_code": 404,
        "detail": "The requested conversation does not exist"
    },
    ErrorCode.CONVERSATION_ALREADY_CLOSED: {
        "message": "Conversation is already closed",
        "status_code": 400,
        "detail": "Cannot perform action on closed conversation"
    },
    ErrorCode.CONVERSATION_ALREADY_ACTIVE: {
        "message": "Conversation is already active",
        "status_code": 409,
        "detail": "An active or pending conversation already exists for this customer"
    },
    ErrorCode.CONVERSATION_ACCESS_DENIED: {
        "message": "Access denied to conversation",
        "status_code": 403,
        "detail": "You do not have permission to access this conversation"
    },
    ErrorCode.INVALID_CONVERSATION_ID: {
        "message": "Invalid conversation ID",
        "status_code": 400,
        "detail": "The provided conversation ID is not valid"
    },
    ErrorCode.MESSAGE_TOO_LARGE: {
        "message": "Message content exceeds size limit",
        "status_code": 413,
        "detail": "Please reduce the message size and try again"
    },
    
    # Media & Files
    ErrorCode.MEDIA_NOT_FOUND: {
        "message": "Media file not found",
        "status_code": 404,
        "detail": "The requested media file does not exist"
    },
    ErrorCode.MEDIA_TOO_LARGE: {
        "message": "Media file exceeds size limit",
        "status_code": 413,
        "detail": "Please upload a smaller file"
    },
    ErrorCode.MEDIA_INVALID_TYPE: {
        "message": "Unsupported media type",
        "status_code": 400,
        "detail": "Please upload a supported file format"
    },
    
    # Database
    ErrorCode.DATABASE_CONNECTION_ERROR: {
        "message": "Database connection failed",
        "status_code": 503,
        "detail": "Unable to connect to the database"
    },
    ErrorCode.DATABASE_OPERATION_FAILED: {
        "message": "Database operation failed",
        "status_code": 500,
        "detail": "An error occurred while accessing the database"
    },
    
    # Validation
    ErrorCode.VALIDATION_ERROR: {
        "message": "Validation error",
        "status_code": 422,
        "detail": "One or more fields contain invalid data"
    },
    ErrorCode.VALIDATION_REQUIRED_FIELD: {
        "message": "Required field missing",
        "status_code": 422,
        "detail": "Please provide all required fields"
    },
    
    # Rate Limiting
    ErrorCode.RATE_LIMIT_EXCEEDED: {
        "message": "Rate limit exceeded",
        "status_code": 429,
        "detail": "Too many requests. Please try again later"
    },
    
    # System
    ErrorCode.INTERNAL_SERVER_ERROR: {
        "message": "Internal server error",
        "status_code": 500,
        "detail": "An unexpected error occurred. Please try again"
    },
    ErrorCode.SERVICE_UNAVAILABLE: {
        "message": "Service temporarily unavailable",
        "status_code": 503,
        "detail": "The service is currently undergoing maintenance"
    },
    ErrorCode.FEATURE_NOT_IMPLEMENTED: {
        "message": "Feature not implemented",
        "status_code": 501,
        "detail": "This feature is not yet available"
    },
}


def get_error_response(error_code: ErrorCode, custom_detail: str = None) -> Dict[str, Any]:
    """
    Get a standardized error response for the given error code.
    
    Args:
        error_code: The error code to get response for
        custom_detail: Optional custom detail message to override default
        
    Returns:
        Dictionary containing error response data
    """
    error_info = ERROR_MESSAGES.get(error_code, ERROR_MESSAGES[ErrorCode.INTERNAL_SERVER_ERROR])
    
    return {
        "error_code": error_code,
        "message": error_info["message"],
        "detail": custom_detail if custom_detail else error_info["detail"],
        "status_code": error_info["status_code"]
    } 