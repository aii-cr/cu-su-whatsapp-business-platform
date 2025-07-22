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
import time
import uuid
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logger import logger, log_api_request, log_api_response, setup_logging
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
    
    * **Authentication & Authorization**: JWT-based auth with RBAC
    * **Conversation Management**: Full conversation lifecycle with agent assignment
    * **Message Handling**: Support for all WhatsApp message types (text, media, interactive)
    * **WhatsApp Integration**: Webhook processing and Cloud API integration
    * **Media Management**: File upload/download with size validation
    * **Real-time Features**: WebSocket support for live updates
    * **Audit Trail**: Comprehensive logging for compliance
    * **Multi-tenant**: Department-based organization
    
    ### Getting Started
    
    1. Obtain access token via `/auth/users/login`
    2. Include `Authorization: Bearer <token>` header in requests
    3. Use `/whatsapp/webhook` for WhatsApp webhook integration
    4. Monitor system health via `/health` endpoint
    
    ### Authentication
    
    Most endpoints require authentication. Use the login endpoint to obtain JWT tokens.
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
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Request tracking middleware
@app.middleware("http")
async def add_request_tracking(request: Request, call_next):
    """Add request tracking and logging."""
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    # Add request ID to headers
    request.state.request_id = request_id
    
    # Log request
    log_api_request(
        method=request.method,
        path=request.url.path,
        request_id=request_id,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate response time
    response_time = time.time() - start_time
    
    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{response_time:.3f}"
    
    # Log response
    log_api_response(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        response_time=response_time,
        request_id=request_id
    )
    
    return response

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
            "request_id": getattr(request.state, "request_id", None)
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
            "request_id": getattr(request.state, "request_id", None)
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
            "request_id": getattr(request.state, "request_id", None)
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
            "request_id": getattr(request.state, "request_id", None)
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
