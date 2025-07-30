"""Service layer initialization and factory."""

from app.services.whatsapp.message.message_service import message_service
from app.services.whatsapp.conversation.conversation_service import conversation_service
from app.services.audit.audit_service import audit_service
from app.services.whatsapp.whatsapp_service import WhatsAppService
from app.services.whatsapp.automation_service import automation_service
from app.services.websocket.websocket_service import websocket_service
from app.services.auth.auth_service import auth_service
from app.services.system.audit_service import system_audit_service
from app.services.system.database_service import database_service

# Service instances
whatsapp_service = WhatsAppService()

__all__ = [
    "message_service",
    "conversation_service", 
    "audit_service",
    "whatsapp_service",
    "automation_service",
    "websocket_service",
    "auth_service",
    "system_audit_service",
    "database_service"
]