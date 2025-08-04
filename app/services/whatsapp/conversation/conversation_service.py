"""WhatsApp Conversation Service."""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from bson import ObjectId

from app.services.base_service import BaseService
from app.core.logger import logger
from app.config.error_codes import ErrorCode


class ConversationService(BaseService):
    """Service for managing WhatsApp conversations."""
    
    def __init__(self):
        super().__init__()
    
    async def create_conversation(
        self,
        customer_phone: str,
        customer_name: Optional[str] = None,
        department_id: Optional[ObjectId] = None,
        assigned_agent_id: Optional[ObjectId] = None,
        created_by: ObjectId = None,
        priority: str = "normal",
        channel: str = "whatsapp",
        customer_type: str = "individual",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new conversation.
        
        Args:
            customer_phone: Customer's phone number
            customer_name: Customer's name (optional)
            department_id: Department ID (optional)
            assigned_agent_id: Assigned agent ID (optional)
            created_by: User who created the conversation
            priority: Conversation priority (low, normal, high, urgent)
            channel: Communication channel (whatsapp)
            customer_type: Type of customer (individual, business)
            tags: List of tags for the conversation
            metadata: Additional metadata
            
        Returns:
            Created conversation document
        """
        db = await self._get_db()
        
        # Check for existing active conversation
        existing_conversation = await db.conversations.find_one({
            "customer_phone": customer_phone,
            "status": {"$in": ["active", "pending"]}
        })
        
        if existing_conversation:
            logger.warning(f"Active conversation already exists for {customer_phone}")
            return existing_conversation
        
        # Prepare conversation data
        conversation_data = {
            "customer_phone": customer_phone,
            "customer_name": customer_name,
            "department_id": department_id,
            "assigned_agent_id": assigned_agent_id,
            "status": "pending",
            "priority": priority,
            "channel": channel,
            "customer_type": customer_type,
            "tags": tags or [],
            "metadata": metadata or {},
            "message_count": 0,
            "unread_count": 0,
            "created_by": created_by,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "last_message_at": None
        }
        
        # Insert conversation
        result = await db.conversations.insert_one(conversation_data)
        conversation_id = result.inserted_id
        
        logger.info(f"Created conversation {conversation_id} for {customer_phone}")
        
        # Return created conversation
        return await db.conversations.find_one({"_id": conversation_id})
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a conversation by ID.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation document or None
        """
        try:
            db = await self._get_db()
            return await db.conversations.find_one({"_id": ObjectId(conversation_id)})
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {str(e)}")
            return None
    
    async def find_conversation_by_phone(self, customer_phone: str) -> Optional[Dict[str, Any]]:
        """
        Find conversation by customer phone number.
        
        Args:
            customer_phone: Customer's phone number
            
        Returns:
            Conversation document or None
        """
        db = await self._get_db()
        return await db.conversations.find_one({"customer_phone": customer_phone})
    
    async def list_conversations(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        channel: Optional[str] = None,
        department_id: Optional[ObjectId] = None,
        assigned_agent_id: Optional[ObjectId] = None,
        customer_type: Optional[str] = None,
        has_unread: Optional[bool] = None,
        created_from: Optional[datetime] = None,
        created_to: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """
        List conversations with filtering and pagination.
        
        Returns:
            Dictionary with conversations, total count, and pagination info
        """
        db = await self._get_db()
        
        # Build query
        query = {}
        
        if search:
            query["$or"] = [
                {"customer_name": {"$regex": search, "$options": "i"}},
                {"customer_phone": {"$regex": search, "$options": "i"}}
            ]
        
        if status:
            query["status"] = status
        if priority:
            query["priority"] = priority
        if channel:
            query["channel"] = channel
        if department_id:
            query["department_id"] = department_id
        if assigned_agent_id:
            query["assigned_agent_id"] = assigned_agent_id
        if customer_type:
            query["customer_type"] = customer_type
        if has_unread is not None:
            query["unread_count"] = {"$gt": 0} if has_unread else {"$eq": 0}
        if created_from:
            query.setdefault("created_at", {})["$gte"] = created_from
        if created_to:
            query.setdefault("created_at", {})["$lte"] = created_to
        if tags:
            query["tags"] = {"$in": tags}
        
        # Count total
        total = await db.conversations.count_documents(query)
        
        # Calculate pagination
        skip = (page - 1) * per_page
        pages = (total + per_page - 1) // per_page
        
        # Get conversations
        sort_direction = 1 if sort_order == "asc" else -1
        conversations = await db.conversations.find(query).sort(
            sort_by, sort_direction
        ).skip(skip).limit(per_page).to_list(per_page)
        
        return {
            "conversations": conversations,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages
        }
    
    async def update_conversation(
        self,
        conversation_id: str,
        update_data: Dict[str, Any],
        updated_by: ObjectId = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update a conversation.
        
        Args:
            conversation_id: Conversation ID
            update_data: Data to update
            updated_by: User who made the update
            
        Returns:
            Updated conversation document or None
        """
        try:
            db = await self._get_db()
            
            # Add update timestamp
            update_data["updated_at"] = datetime.now(timezone.utc)
            if updated_by:
                update_data["updated_by"] = updated_by
            
            result = await db.conversations.update_one(
                {"_id": ObjectId(conversation_id)},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                return None
            
            return await db.conversations.find_one({"_id": ObjectId(conversation_id)})
            
        except Exception as e:
            logger.error(f"Error updating conversation {conversation_id}: {str(e)}")
            return None
    
    async def delete_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Delete a conversation and all associated messages.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Deleted conversation data if successful, None otherwise
        """
        try:
            db = await self._get_db()
            
            # Get conversation data before deletion
            conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
            if not conversation:
                return None
            
            # Delete all messages first
            messages_deleted = await db.messages.delete_many({
                "conversation_id": ObjectId(conversation_id)
            })
            
            # Delete conversation
            result = await db.conversations.delete_one({
                "_id": ObjectId(conversation_id)
            })
            
            logger.info(f"Deleted conversation {conversation_id} and {messages_deleted.deleted_count} messages")
            return conversation if result.deleted_count > 0 else None
            
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {str(e)}")
            return None
    
    async def increment_message_count(self, conversation_id: str) -> bool:
        """
        Increment message count for a conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            True if updated successfully
        """
        try:
            db = await self._get_db()
            result = await db.conversations.update_one(
                {"_id": ObjectId(conversation_id)},
                {
                    "$inc": {"message_count": 1},
                    "$set": {
                        "last_message_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error incrementing message count for {conversation_id}: {str(e)}")
            return False
    
    async def update_unread_count(self, conversation_id: str, increment: bool = True) -> bool:
        """
        Update unread count for a conversation.
        
        Args:
            conversation_id: Conversation ID
            increment: True to increment, False to reset to 0
            
        Returns:
            True if updated successfully
        """
        try:
            db = await self._get_db()
            
            if increment:
                update_data = {"$inc": {"unread_count": 1}}
            else:
                update_data = {"$set": {"unread_count": 0}}
            
            result = await db.conversations.update_one(
                {"_id": ObjectId(conversation_id)},
                update_data
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating unread count for {conversation_id}: {str(e)}")
            return False


# Global conversation service instance
conversation_service = ConversationService() 