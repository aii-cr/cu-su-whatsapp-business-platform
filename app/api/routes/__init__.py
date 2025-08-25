"""
API routes package for the WhatsApp Business Platform.

Routes are organized into logical categories:
- auth: Authentication and user management routes
- whatsapp: WhatsApp API integration and chat routes
- business: Department and company management routes
- system: System administration and audit routes
"""

from datetime import datetime, timezone

from fastapi import APIRouter

# Import route modules
from .auth.users import router as users_router
from .auth.roles import router as roles_router
from .auth.permissions import router as permissions_router
from .websocket import router as websocket_router
from .whatsapp.chat.conversations import router as conversations_router
from .whatsapp.chat.messages import router as messages_router
from .whatsapp.chat.tags import router as tags_router
from .whatsapp.webhook import router as webhook_router
from .business import router as business_router
from .ai import agent_router, memory_router, summarizer_router, writer_router
from .reservations import router as reservations_router

# Create main API router
api_router = APIRouter()

# Include authentication routes
api_router.include_router(users_router, prefix="/auth")
api_router.include_router(roles_router, prefix="/auth")
api_router.include_router(permissions_router, prefix="/auth")

# Include WhatsApp routes
api_router.include_router(webhook_router)

# Include WhatsApp chat routes
api_router.include_router(conversations_router)
api_router.include_router(messages_router)
api_router.include_router(tags_router)

# Include business routes
api_router.include_router(business_router)

# Include reservations routes (open endpoints)
api_router.include_router(reservations_router)

# Include AI routes
api_router.include_router(agent_router)
api_router.include_router(memory_router)
api_router.include_router(summarizer_router)
api_router.include_router(writer_router, prefix="/ai/writer", tags=["AI Writer"])

# Include WebSocket routes
api_router.include_router(websocket_router)


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
        await database.client.admin.command("ping")
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
        },
    }


# System routes
from .system.audit.get_logs import router as audit_router

# Include system routes
api_router.include_router(audit_router, prefix="/system")

# TODO: Add these routes as they are implemented
# from .whatsapp.media import router as media_router
# from .business.departments import router as departments_router
# from .business.company import router as company_router

# api_router.include_router(media_router, prefix="/media")
# api_router.include_router(departments_router, prefix="/departments")
# api_router.include_router(company_router, prefix="/company")

__all__ = ["api_router"]
