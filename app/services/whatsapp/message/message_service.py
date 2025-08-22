"""WhatsApp Message Service."""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from bson import ObjectId

from app.services.base_service import BaseService
from app.core.logger import logger
from app.config.error_codes import ErrorCode


class MessageService(BaseService):
    """Service for managing WhatsApp messages."""
    
    def __init__(self):
        super().__init__()
    
    async def create_message(
        self,
        conversation_id: str,
        message_type: str,
        direction: str,
        sender_role: str,
        sender_id: Optional[ObjectId] = None,
        sender_phone: Optional[str] = None,
        sender_name: Optional[str] = None,
        text_content: Optional[str] = None,
        media_url: Optional[str] = None,
        media_metadata: Optional[Dict[str, Any]] = None,
        template_data: Optional[Dict[str, Any]] = None,
        interactive_content: Optional[Dict[str, Any]] = None,
        location_data: Optional[Dict[str, Any]] = None,
        contact_data: Optional[Dict[str, Any]] = None,
        whatsapp_message_id: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        is_automated: bool = False,
        whatsapp_data: Optional[Dict[str, Any]] = None,
        status: str = "sent"
    ) -> Dict[str, Any]:
        """
        Create a new message.
        
        Args:
            conversation_id: Conversation ID
            message_type: Type of message (text, template, media, etc.)
            direction: Message direction (inbound, outbound)
            sender_role: Role of sender (customer, agent, system)
            sender_id: ID of the sender
            sender_phone: Phone number of sender
            sender_name: Name of sender
            text_content: Text content of message
            media_url: URL of media file
            media_metadata: Metadata for media
            template_data: Template message data
            interactive_content: Interactive message data
            location_data: Location message data
            contact_data: Contact message data
            whatsapp_message_id: WhatsApp message ID
            reply_to_message_id: ID of message being replied to
            is_automated: Whether message is automated
            whatsapp_data: WhatsApp API response data
            status: Message status (sent, delivered, read, failed)
            
        Returns:
            Created message document
        """
        db = await self._get_db()
        
        message_data = {
            "conversation_id": ObjectId(conversation_id),
            "whatsapp_message_id": whatsapp_message_id,
            "type": message_type,
            "direction": direction,
            "sender_role": sender_role,
            "sender_id": sender_id,
            "sender_phone": sender_phone,
            "sender_name": sender_name,
            "text_content": text_content,
            "media_url": media_url,
            "media_metadata": media_metadata,
            "template_data": template_data,
            "interactive_content": interactive_content,
            "location_data": location_data,
            "contact_data": contact_data,
            "status": status,
            "timestamp": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "reply_to_message_id": ObjectId(reply_to_message_id) if reply_to_message_id else None,
            "is_automated": is_automated,
            "whatsapp_data": whatsapp_data or {}
        }
        
        # Add status-specific timestamps
        if status == "sent":
            message_data["sent_at"] = datetime.utcnow()
        
        result = await db.messages.insert_one(message_data)
        message_id = result.inserted_id
        
        logger.info(f"Created message {message_id} for conversation {conversation_id}")
        
        # Auto-assign conversation if agent sends first message and conversation is unassigned
        if (sender_role == "agent" and sender_id and 
            direction == "outbound" and not is_automated):
            
            # Check if conversation is unassigned
            conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
            if conversation and not conversation.get("assigned_agent_id"):
                logger.info(f"🤖 [AUTO_ASSIGN] Auto-assigning conversation {conversation_id} to agent {sender_id}")
                
                # Auto-assign the conversation directly here to avoid circular import
                try:
                    # Update conversation with assigned agent
                    update_data = {
                        "assigned_agent_id": sender_id,
                        "updated_at": datetime.now(timezone.utc),
                        "status": "active"  # Activate the conversation when assigned
                    }
                    
                    result = await db.conversations.update_one(
                        {"_id": ObjectId(conversation_id)},
                        {"$set": update_data}
                    )
                    
                    if result.modified_count > 0:
                        # Import audit service here to avoid circular import
                        from app.services.audit.audit_service import audit_service
                        
                        # Log audit event
                        await audit_service.log_event(
                            action="conversation_auto_assigned",
                            actor_id=str(sender_id),
                            conversation_id=conversation_id,
                            payload={
                                "agent_id": str(sender_id),
                                "previous_agent_id": None,
                                "claim_method": "auto"
                            },
                            correlation_id=None
                        )
                        
                        logger.info(f"✅ [AUTO_ASSIGN] Conversation {conversation_id} auto-assigned to agent {sender_id}")
                        
                        # Broadcast assignment update to all dashboard subscribers
                        try:
                            from app.services.websocket.websocket_service import manager
                            
                            # Get agent name for the broadcast
                            agent_doc = await db.users.find_one({"_id": sender_id}, {"name": 1, "email": 1})
                            agent_name = agent_doc.get("name") or agent_doc.get("email") if agent_doc else "Unknown Agent"
                            
                            await manager.broadcast_conversation_assignment_update(
                                conversation_id=conversation_id,
                                assigned_agent_id=str(sender_id),
                                agent_name=agent_name
                            )
                        except Exception as ws_error:
                            logger.error(f"❌ [AUTO_ASSIGN] Error broadcasting assignment update: {str(ws_error)}")
                except Exception as e:
                    logger.error(f"❌ [AUTO_ASSIGN] Error auto-assigning conversation {conversation_id}: {str(e)}")
        
        # Return created message
        return await db.messages.find_one({"_id": message_id})
    
    async def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a message by ID.
        
        Args:
            message_id: Message ID
            
        Returns:
            Message document or None
        """
        try:
            db = await self._get_db()
            return await db.messages.find_one({"_id": ObjectId(message_id)})
        except Exception as e:
            logger.error(f"Error getting message {message_id}: {str(e)}")
            return None
    
    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "timestamp",
        sort_order: str = "asc"
    ) -> Dict[str, Any]:
        """
        Get messages for a conversation with pagination.
        
        Args:
            conversation_id: Conversation ID
            limit: Number of messages to return
            offset: Number of messages to skip
            sort_by: Field to sort by
            sort_order: Sort order (asc, desc)
            
        Returns:
            Dictionary with messages and total count
        """
        try:
            db = await self._get_db()
            
            # Get messages
            sort_direction = 1 if sort_order == "asc" else -1
            messages = await db.messages.find(
                {"conversation_id": ObjectId(conversation_id)}
            ).sort(sort_by, sort_direction).skip(offset).limit(limit).to_list(limit)
            
            # Count total
            total = await db.messages.count_documents(
                {"conversation_id": ObjectId(conversation_id)}
            )
            
            return {
                "messages": messages,
                "total": total,
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            logger.error(f"Error getting messages for conversation {conversation_id}: {str(e)}")
            return {"messages": [], "total": 0, "limit": limit, "offset": offset}
    
    async def update_message_status(
        self,
        message_id: str,
        status: str,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        whatsapp_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update message status.
        
        Args:
            message_id: Message ID
            status: New status (sent, delivered, read, failed)
            error_code: Error code if failed
            error_message: Error message if failed
            whatsapp_data: Additional WhatsApp data
            
        Returns:
            True if updated successfully
        """
        try:
            db = await self._get_db()
            
            update_data = {
                "status": status,
                "updated_at": datetime.now(timezone.utc)
            }
            
            # Add status-specific timestamps
            if status == "sent":
                update_data["sent_at"] = datetime.now(timezone.utc)
            elif status == "delivered":
                update_data["delivered_at"] = datetime.now(timezone.utc)
            elif status == "read":
                update_data["read_at"] = datetime.now(timezone.utc)
            elif status == "failed":
                update_data["failed_at"] = datetime.now(timezone.utc)
                if error_code:
                    update_data["error_code"] = error_code
                if error_message:
                    update_data["error_message"] = error_message
            
            # Add WhatsApp data if provided
            if whatsapp_data:
                for key, value in whatsapp_data.items():
                    update_data[f"whatsapp_data.{key}"] = value
            
            result = await db.messages.update_one(
                {"_id": ObjectId(message_id)},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating message status {message_id}: {str(e)}")
            return False
    
    async def find_message_by_whatsapp_id(self, whatsapp_message_id: str) -> Optional[Dict[str, Any]]:
        """
        Find message by WhatsApp message ID.
        
        Args:
            whatsapp_message_id: WhatsApp message ID
            
        Returns:
            Message document or None
        """
        db = await self._get_db()
        return await db.messages.find_one({"whatsapp_message_id": whatsapp_message_id})
    
    async def delete_message(self, message_id: str) -> bool:
        """
        Delete a message.
        
        Args:
            message_id: Message ID
            
        Returns:
            True if deleted successfully
        """
        try:
            db = await self._get_db()
            result = await db.messages.delete_one({"_id": ObjectId(message_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting message {message_id}: {str(e)}")
            return False


# Global message service instance
message_service = MessageService() 