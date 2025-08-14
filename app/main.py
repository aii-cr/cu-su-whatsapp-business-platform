"""
Main FastAPI application for WhatsApp Business Platform Backend.
Production-ready configuration with comprehensive middleware, error handling, and API routes.
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logger import logger, setup_logging
from app.core.middleware import CorrelationMiddleware, SessionActivityMiddleware, RequestLoggingMiddleware
from app.api.routes import api_router
from app.db.client import database
from app.config.error_codes import ErrorCode

# Setup logging
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    
    # Startup
    logger.info("Starting WhatsApp Business Platform Backend")
    
    # Connect to MongoDB
    try:
        await database.connect()
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise
    
    # Initialize other services
    logger.info(f"Application initialized in {settings.ENVIRONMENT} environment")
    
    yield
    
    # Shutdown
    logger.info("Shutting down WhatsApp Business Platform Backend")
    
    # Close MongoDB connection
    try:
        await database.disconnect()
        logger.info("MongoDB connection closed")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {str(e)}")

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## WhatsApp Business Platform Backend API
    
    A comprehensive backend for WhatsApp Business messaging platform with:
    
    * **Authentication & Authorization**: Cookie-based session auth with RBAC
    * **Conversation Management**: Full conversation lifecycle with agent assignment
    * **Message Handling**: Support for all WhatsApp message types (text, media, interactive)
    * **WhatsApp Integration**: Webhook processing and Cloud API integration
    * **Media Management**: File upload/download with size validation
    * **Real-time Features**: WebSocket support for live updates
    * **Audit Trail**: Comprehensive logging for compliance
    * **Multi-tenant**: Department-based organization
    
    ### Getting Started
    
    1. Login via `/auth/users/login` to get session cookie
    2. Session cookie is automatically included in subsequent requests
    3. Use `/whatsapp/webhook` for WhatsApp webhook integration
    4. Monitor system health via `/health` endpoint
    
    ### Authentication
    
    Most endpoints require authentication. Use the login endpoint to obtain session cookies.
    Sessions expire after 160 minutes or 15 minutes of inactivity.
    """,
    docs_url=settings.DOCS_URL if settings.ENVIRONMENT != "production" else None,
    redoc_url=settings.REDOC_URL if settings.ENVIRONMENT != "production" else None,
    openapi_url=settings.OPENAPI_URL,
    lifespan=lifespan
)

# Add security middleware
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.yourdomain.com", "yourdomain.com"]
    )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-Correlation-ID",
        "X-Response-Time",
        "Cache-Control",
        "Pragma",
        "Expires",
        "Last-Modified",
        "If-Modified-Since",
        "If-None-Match",
        "ETag",
        "Range",
        "If-Range",
        "Accept-Ranges",
        "Content-Range",
        "Content-Disposition",
        "Content-Encoding",
        "Content-Length",
        "Transfer-Encoding",
        "Connection",
        "Upgrade",
        "Sec-WebSocket-Key",
        "Sec-WebSocket-Version",
        "Sec-WebSocket-Protocol",
        "Sec-WebSocket-Extensions",
        "Sec-WebSocket-Accept",
        "Cookie",
        "Set-Cookie",
        "X-Forwarded-For",
        "X-Forwarded-Proto",
        "X-Forwarded-Host",
        "X-Real-IP",
        "X-Forwarded-Port",
        "X-Forwarded-Server",
        "X-Forwarded-Ssl",
        "X-Forwarded-Prefix",
        "X-Original-URI",
        "X-Original-Method",
        "X-Original-Host",
        "X-Original-Port",
        "X-Original-Proto",
        "X-Original-Server",
        "X-Original-Ssl",
        "X-Original-Prefix",
        "X-Original-URI",
        "X-Original-Method",
        "X-Original-Host",
        "X-Original-Port",
        "X-Original-Proto",
        "X-Original-Server",
        "X-Original-Ssl",
        "X-Original-Prefix",
        "*"
    ],
    expose_headers=[
        "X-Correlation-ID",
        "X-Response-Time",
        "X-Request-ID",
        "Content-Length",
        "Content-Range",
        "Content-Disposition",
        "Content-Encoding",
        "Content-Type",
        "Cache-Control",
        "ETag",
        "Last-Modified",
        "Expires",
        "Pragma",
        "Set-Cookie",
        "X-Powered-By",
        "Server",
        "Date",
        "Connection",
        "Keep-Alive",
        "Transfer-Encoding",
        "Upgrade",
        "Sec-WebSocket-Accept",
        "Sec-WebSocket-Protocol",
        "Sec-WebSocket-Extensions"
    ],
    max_age=86400,  # 24 hours
)

# Setup custom middleware (correlation ID, session activity, request logging)
app.add_middleware(CorrelationMiddleware)
app.add_middleware(SessionActivityMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": getattr(exc, "detail", "HTTP_ERROR"),
            "error_message": exc.detail,
            "request_id": getattr(request.state, "correlation_id", None)
        }
    )

@app.exception_handler(StarletteHTTPException)
async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle Starlette HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": f"HTTP_{exc.status_code}",
            "error_message": exc.detail,
            "request_id": getattr(request.state, "correlation_id", None)
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.warning(f"Validation error on {request.method} {request.url.path}: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error_code": ErrorCode.VALIDATION_ERROR,
            "error_message": "Request validation failed",
            "details": exc.errors(),
            "request_id": getattr(request.state, "correlation_id", None)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_code": ErrorCode.INTERNAL_SERVER_ERROR,
            "error_message": "Internal server error" if settings.ENVIRONMENT == "production" else str(exc),
            "request_id": getattr(request.state, "correlation_id", None)
        }
    )

# Include API routes
app.include_router(api_router, prefix=settings.API_PREFIX)

# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with basic API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": f"{settings.API_PREFIX}{settings.DOCS_URL}" if settings.DOCS_URL else None,
        "health_url": f"{settings.API_PREFIX}/health",
        "webhook_url": f"{settings.API_PREFIX}/whatsapp/webhook"
    }

if __name__ == "__main__":
    import uvicorn
    
    # Development server configuration
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )
