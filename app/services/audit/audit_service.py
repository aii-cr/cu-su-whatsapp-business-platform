"""
Domain-level audit logging service for WhatsApp Business Platform.
Provides comprehensive audit logging for all business activities.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.config import settings
from app.core.logger import logger
from app.db.client import database


class AuditService:
    """
    Service for domain-level audit logging.

    Tracks all business activities in WhatsApp conversations including:
    - Message sending/receiving
    - Agent transfers
    - Conversation status changes
    - Tag and note management
    - Priority changes
    """

    @staticmethod
    async def log_event(
        action: str,
        actor_id: Optional[str] = None,
        actor_name: Optional[str] = None,
        customer_phone: Optional[str] = None,
        conversation_id: Optional[str] = None,
        department_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Log an audit event with domain-specific schema.

        Args:
            action: The action performed (e.g., message_sent, agent_transfer)
            actor_id: ID of the user/system performing the action
            actor_name: Name of the user/system performing the action
            customer_phone: Phone number of the customer involved
            conversation_id: ID of the conversation involved
            department_id: ID of the department involved
            payload: Additional action-specific data
            metadata: Additional context and correlation data
            correlation_id: Request correlation ID for tracing

        Returns:
            str: The ID of the created audit log entry, None if failed
        """
        try:
            # Prepare metadata with correlation ID
            audit_metadata = metadata or {}
            if correlation_id:
                audit_metadata["correlation_id"] = correlation_id

            # Create audit log document
            audit_doc = {
                "conversation_id": ObjectId(conversation_id) if conversation_id else None,
                "customer_phone": customer_phone,
                "actor_id": ObjectId(actor_id) if actor_id else None,
                "actor_name": actor_name,
                "department_id": ObjectId(department_id) if department_id else None,
                "action": action,
                "payload": payload or {},
                "created_at": datetime.now(timezone.utc),
                "metadata": audit_metadata,
            }

            # Insert with write concern for durability
            collection: AsyncIOMotorCollection = database.db.audit_logs
            result = await collection.insert_one(audit_doc, write_concern={"w": 1, "j": True})

            # Log successful audit entry
            logger.info(
                f"Audit event logged: {action}",
                extra={
                    "audit_id": str(result.inserted_id),
                    "action": action,
                    "actor_id": actor_id,
                    "conversation_id": conversation_id,
                    "correlation_id": correlation_id,
                },
            )

            return str(result.inserted_id)

        except Exception as e:
            logger.error(
                f"Failed to log audit event: {action}",
                extra={
                    "error": str(e),
                    "action": action,
                    "actor_id": actor_id,
                    "conversation_id": conversation_id,
                    "correlation_id": correlation_id,
                },
                exc_info=True,
            )
            return None

    @staticmethod
    async def log_message_sent(
        actor_id: str,
        actor_name: str,
        conversation_id: str,
        customer_phone: str,
        department_id: Optional[str] = None,
        message_type: str = "text",
        message_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Log message sent event."""
        return await AuditService.log_event(
            action="message_sent",
            actor_id=actor_id,
            actor_name=actor_name,
            customer_phone=customer_phone,
            conversation_id=conversation_id,
            department_id=department_id,
            payload={"message_type": message_type, "message_id": message_id},
            correlation_id=correlation_id,
        )

    @staticmethod
    async def log_agent_transfer(
        actor_id: str,
        actor_name: str,
        conversation_id: str,
        customer_phone: str,
        from_department_id: Optional[str] = None,
        to_department_id: Optional[str] = None,
        from_agent_id: Optional[str] = None,
        to_agent_id: Optional[str] = None,
        reason: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Log agent transfer event."""
        return await AuditService.log_event(
            action="agent_transfer",
            actor_id=actor_id,
            actor_name=actor_name,
            customer_phone=customer_phone,
            conversation_id=conversation_id,
            department_id=to_department_id,
            payload={
                "from_department_id": from_department_id,
                "to_department_id": to_department_id,
                "from_agent_id": from_agent_id,
                "to_agent_id": to_agent_id,
                "reason": reason,
            },
            correlation_id=correlation_id,
        )

    @staticmethod
    async def log_conversation_closed(
        actor_id: str,
        actor_name: str,
        conversation_id: str,
        customer_phone: str,
        department_id: Optional[str] = None,
        reason: Optional[str] = None,
        resolution: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Log conversation closed event."""
        return await AuditService.log_event(
            action="conversation_closed",
            actor_id=actor_id,
            actor_name=actor_name,
            customer_phone=customer_phone,
            conversation_id=conversation_id,
            department_id=department_id,
            payload={"reason": reason, "resolution": resolution},
            correlation_id=correlation_id,
        )

    @staticmethod
    async def log_tag_added(
        actor_id: str,
        actor_name: str,
        conversation_id: str,
        customer_phone: str,
        department_id: Optional[str] = None,
        tag_name: Optional[str] = None,
        tag_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Log tag added event."""
        return await AuditService.log_event(
            action="tag_added",
            actor_id=actor_id,
            actor_name=actor_name,
            customer_phone=customer_phone,
            conversation_id=conversation_id,
            department_id=department_id,
            payload={"tag_name": tag_name, "tag_id": tag_id},
            correlation_id=correlation_id,
        )

    @staticmethod
    async def log_note_added(
        actor_id: str,
        actor_name: str,
        conversation_id: str,
        customer_phone: str,
        department_id: Optional[str] = None,
        note_id: Optional[str] = None,
        note_type: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Log note added event."""
        return await AuditService.log_event(
            action="note_added",
            actor_id=actor_id,
            actor_name=actor_name,
            customer_phone=customer_phone,
            conversation_id=conversation_id,
            department_id=department_id,
            payload={"note_id": note_id, "note_type": note_type},
            correlation_id=correlation_id,
        )

    @staticmethod
    async def log_status_changed(
        actor_id: str,
        actor_name: str,
        conversation_id: str,
        customer_phone: str,
        department_id: Optional[str] = None,
        from_status: Optional[str] = None,
        to_status: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Log status change event."""
        return await AuditService.log_event(
            action="status_changed",
            actor_id=actor_id,
            actor_name=actor_name,
            customer_phone=customer_phone,
            conversation_id=conversation_id,
            department_id=department_id,
            payload={"from_status": from_status, "to_status": to_status},
            correlation_id=correlation_id,
        )

    @staticmethod
    async def log_priority_changed(
        actor_id: str,
        actor_name: str,
        conversation_id: str,
        customer_phone: str,
        department_id: Optional[str] = None,
        from_priority: Optional[str] = None,
        to_priority: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Log priority change event."""
        return await AuditService.log_event(
            action="priority_changed",
            actor_id=actor_id,
            actor_name=actor_name,
            customer_phone=customer_phone,
            conversation_id=conversation_id,
            department_id=department_id,
            payload={"from_priority": from_priority, "to_priority": to_priority},
            correlation_id=correlation_id,
        )
