"""Service layer initialization and factory."""

from app.services.whatsapp.message.message_service import MessageService
from app.services.whatsapp.conversation.conversation_service import ConversationService
from app.services.audit.audit_service import AuditService
from app.services.whatsapp.whatsapp_service import WhatsAppService
from app.services.whatsapp.automation_service import automation_service
from app.services.websocket.websocket_service import websocket_service
from app.services.auth.auth_service import AuthService
from app.services.system.audit_service import SystemAuditService

# Service instances
message_service = MessageService()
conversation_service = ConversationService()
audit_service = AuditService()
whatsapp_service = WhatsAppService()
auth_service = AuthService()
system_audit_service = SystemAuditService()

__all__ = [
    "message_service",
    "conversation_service", 
    "audit_service",
    "whatsapp_service",
    "automation_service",
    "websocket_service",
    "auth_service",
    "system_audit_service"
]