"""
API routes package for the WhatsApp Business Platform.

Routes are organized into logical categories:
- auth: Authentication and user management routes
- chat: Conversation and messaging routes  
- business: Department and company management routes
- system: System administration and audit routes
- whatsapp: WhatsApp API integration routes
"""

from fastapi import APIRouter
from datetime import datetime, timezone

# Import route modules
from .auth.users import router as users_router
from .whatsapp.webhook import router as webhook_router
from .chat.conversations import router as conversations_router
from .chat.messages import router as messages_router

# Create main API router
api_router = APIRouter()

# Include authentication routes
api_router.include_router(users_router, prefix="/auth")

# Include WhatsApp routes
api_router.include_router(webhook_router)

# Include chat routes
api_router.include_router(conversations_router)
api_router.include_router(messages_router)

# Health check endpoint
@api_router.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    from app.core.config import settings
    from app.db.client import database
    
    # Check database connectivity
    try:
        db = database.db
        await db.admin.command("ping")
        database_status = "healthy"
    except Exception as e:
        database_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": database_status,
        "services": {
            "whatsapp_api": "configured" if settings.WHATSAPP_ACCESS_TOKEN else "not_configured",
            "mongodb": database_status,
            "redis": "not_implemented",  # TODO: Add Redis health check
        }
    }

# TODO: Add these routes as they are implemented
# from .chat.messages import router as messages_router
# from .chat.media import router as media_router
# from .business.departments import router as departments_router
# from .business.company import router as company_router
# from .system.audit import router as audit_router

# api_router.include_router(messages_router, prefix="/messages")
# api_router.include_router(media_router, prefix="/media")
# api_router.include_router(departments_router, prefix="/departments")
# api_router.include_router(company_router, prefix="/company")
# api_router.include_router(audit_router, prefix="/system")

__all__ = ["api_router"] 