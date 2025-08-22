"""WhatsApp Conversation Service."""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from bson import ObjectId

from app.services.base_service import BaseService
from app.core.logger import logger
from app.config.error_codes import ErrorCode
from app.services.audit.audit_service import audit_service


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
            "ai_autoreply_enabled": True,  # Default AI auto-reply to ON for new conversations
            "created_by": created_by,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
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
            conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
            
            if conversation:
                # Ensure required fields have default values if missing
                if "customer_type" not in conversation or conversation["customer_type"] is None:
                    conversation["customer_type"] = "individual"
                if "priority" not in conversation or conversation["priority"] is None:
                    conversation["priority"] = "normal"
                if "channel" not in conversation or conversation["channel"] is None:
                    conversation["channel"] = "whatsapp"
                if "status" not in conversation or conversation["status"] is None:
                    conversation["status"] = "pending"
                
                # Get tags for this conversation
                conversation_tags = await db.conversation_tags.find({
                    "conversation_id": ObjectId(conversation_id)
                }).sort("assigned_at", 1).to_list(length=None)
                
                # Convert to tag objects for frontend
                tags = []
                for conv_tag in conversation_tags:
                    tags.append({
                        "id": str(conv_tag["tag_id"]),
                        "name": conv_tag["tag_name"],
                        "slug": conv_tag.get("tag_slug", conv_tag["tag_name"].lower().replace(" ", "-")),
                        "display_name": conv_tag["tag_name"],
                        "category": conv_tag.get("tag_category", "general"),
                        "color": conv_tag["tag_color"],
                        "usage_count": 0  # Not relevant for conversation detail
                    })
                
                conversation["tags"] = tags
            
            return conversation
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
        is_archived: Optional[bool] = None,
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
        if is_archived is not None:
            query["is_archived"] = bool(is_archived)
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
        
        # Populate tags for each conversation and ensure required fields
        for conversation in conversations:
            conversation_id = conversation["_id"]
            
            # Ensure required fields have default values if missing
            if "customer_type" not in conversation or conversation["customer_type"] is None:
                conversation["customer_type"] = "individual"
            if "priority" not in conversation or conversation["priority"] is None:
                conversation["priority"] = "normal"
            if "channel" not in conversation or conversation["channel"] is None:
                conversation["channel"] = "whatsapp"
            if "status" not in conversation or conversation["status"] is None:
                conversation["status"] = "pending"
            
            # Get tags for this conversation
            conversation_tags = await db.conversation_tags.find({
                "conversation_id": conversation_id
            }).sort("assigned_at", 1).to_list(length=None)
            
            # Convert to tag objects for frontend
            tags = []
            for conv_tag in conversation_tags:
                tags.append({
                    "id": str(conv_tag["tag_id"]),
                    "name": conv_tag["tag_name"],
                    "slug": conv_tag.get("tag_slug", conv_tag["tag_name"].lower().replace(" ", "-")),
                    "display_name": conv_tag["tag_name"],
                    "category": conv_tag.get("tag_category", "general"),
                    "color": conv_tag["tag_color"],
                    "usage_count": 0  # Not relevant for conversation list
                })
            
            conversation["tags"] = tags
        
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
            update_data["updated_at"] = datetime.utcnow()
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
    
    async def toggle_ai_autoreply(
        self,
        conversation_id: str,
        enabled: bool,
        updated_by: ObjectId = None
    ) -> Optional[Dict[str, Any]]:
        """
        Toggle AI auto-reply for a conversation.
        
        Args:
            conversation_id: Conversation ID
            enabled: Whether to enable or disable AI auto-reply
            updated_by: User who made the change
            
        Returns:
            Updated conversation document or None
        """
        try:
            db = await self._get_db()
            
            # Get current conversation to check current state
            current_conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
            if not current_conversation:
                logger.warning(f"No conversation found with ID {conversation_id}")
                return None
            
            current_state = current_conversation.get("ai_autoreply_enabled", True)
            
            # Log the toggle action
            action = "enabled" if enabled else "disabled"
            logger.info(f"AI auto-reply {action} for conversation {conversation_id} (was: {current_state})")
            
            # Update the conversation
            update_data = {
                "ai_autoreply_enabled": enabled,
                "updated_at": datetime.utcnow()
            }
            if updated_by:
                update_data["updated_by"] = updated_by
            
            result = await db.conversations.update_one(
                {"_id": ObjectId(conversation_id)},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                logger.warning(f"No conversation found with ID {conversation_id}")
                return None
            
            # Return updated conversation
            updated_conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
            
            # Log the audit event
            await audit_service.log_event(
                action="conversation.ai_autoreply.toggle",
                actor_id=str(updated_by) if updated_by else None,
                conversation_id=conversation_id,
                payload={
                    "ai_autoreply_enabled": enabled,
                    "previous_state": current_state
                }
            )
            
            return updated_conversation
            
        except Exception as e:
            logger.error(f"Error toggling AI auto-reply for conversation {conversation_id}: {str(e)}")
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
                        "last_message_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
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
    
    async def get_conversation_with_messages(
        self,
        conversation_id: str,
        user_id: str,
        is_super_admin: bool = False,
        messages_limit: int = 50,
        messages_offset: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Get conversation with recent messages in a single optimized query.
        
        This method uses MongoDB aggregation to fetch conversation + messages
        efficiently, reducing the number of database round trips.
        
        Args:
            conversation_id: Conversation ID
            user_id: Current user ID for permission checking
            is_super_admin: Whether user is super admin
            messages_limit: Number of messages to return
            messages_offset: Number of messages to skip
            
        Returns:
            Dictionary with conversation, messages, total count, and access info
        """
        try:
            db = await self._get_db()
            
            # First get conversation to check permissions
            conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
            
            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found")
                return None
            
            # Check access permissions
            has_access = is_super_admin
            if not has_access:
                # Check if user is assigned to conversation or has read_all permission
                has_access = (
                    conversation.get("assigned_agent_id") == ObjectId(user_id) or
                    conversation.get("created_by") == ObjectId(user_id)
                    # Note: Additional permission check for read_all would need auth service
                )
            
            if not has_access:
                return {
                    "conversation": conversation,
                    "messages": [],
                    "messages_total": 0,
                    "has_access": False
                }
            
            # Use aggregation pipeline to get messages efficiently
            pipeline = [
                # Match messages for this conversation
                {
                    "$match": {
                        "conversation_id": ObjectId(conversation_id)
                    }
                },
                # Sort by timestamp descending (newest first)
                {
                    "$sort": {
                        "timestamp": -1
                    }
                },
                # Facet to get both count and paginated results
                {
                    "$facet": {
                        "messages": [
                            {"$skip": messages_offset},
                            {"$limit": messages_limit},
                            {"$sort": {"timestamp": 1}}  # Re-sort for display order
                        ],
                        "total_count": [
                            {"$count": "count"}
                        ]
                    }
                }
            ]
            
            # Execute aggregation
            result = await db.messages.aggregate(pipeline).to_list(1)
            
            if result:
                messages = result[0]["messages"]
                total_count = result[0]["total_count"][0]["count"] if result[0]["total_count"] else 0
            else:
                messages = []
                total_count = 0
            
            # Calculate initial unread count for WhatsApp-like banner
            # Count inbound messages that are not read and are from customers
            unread_count = await db.messages.count_documents({
                "conversation_id": ObjectId(conversation_id),
                "direction": "inbound",
                "status": "received",
                "sender_role": "customer"
            })
            
            logger.info(f"Retrieved conversation {conversation_id} with {len(messages)} messages (total: {total_count}, unread: {unread_count})")
            
            return {
                "conversation": conversation,
                "messages": messages,
                "messages_total": total_count,
                "initial_unread_count": unread_count,
                "has_access": True
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation with messages {conversation_id}: {str(e)}", exc_info=True)
            return None

    # ----------------- Participants Management -----------------
    async def add_participant(self, conversation_id: str, user_id: str, role: str, actor_id: Optional[str] = None, correlation_id: Optional[str] = None) -> bool:
        db = await self._get_db()
        try:
            update = {
                "$addToSet": {
                    "participants": {
                        "_id": ObjectId(),
                        "user_id": ObjectId(user_id),
                        "role": role,
                        "added_at": datetime.utcnow()
                    }
                },
                "$set": {"updated_at": datetime.utcnow()}
            }
            result = await db.conversations.update_one({"_id": ObjectId(conversation_id)}, update)
            if result.modified_count:
                await audit_service.log_event(
                    action="participant_added",
                    actor_id=actor_id,
                    conversation_id=conversation_id,
                    payload={"user_id": user_id, "role": role},
                    correlation_id=correlation_id,
                )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error adding participant: {str(e)}")
            return False

    async def remove_participant(self, conversation_id: str, participant_id: str, actor_id: Optional[str] = None, correlation_id: Optional[str] = None) -> bool:
        db = await self._get_db()
        try:
            result = await db.conversations.update_one(
                {"_id": ObjectId(conversation_id)},
                {"$pull": {"participants": {"_id": ObjectId(participant_id)}}, "$set": {"updated_at": datetime.utcnow()}}
            )
            if result.modified_count:
                await audit_service.log_event(
                    action="participant_removed",
                    actor_id=actor_id,
                    conversation_id=conversation_id,
                    payload={"participant_id": participant_id},
                    correlation_id=correlation_id,
                )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error removing participant: {str(e)}")
            return False

    async def change_participant_role(self, conversation_id: str, participant_id: str, new_role: str, actor_id: Optional[str] = None, correlation_id: Optional[str] = None) -> bool:
        db = await self._get_db()
        try:
            result = await db.conversations.update_one(
                {"_id": ObjectId(conversation_id), "participants._id": ObjectId(participant_id)},
                {"$set": {"participants.$.role": new_role, "updated_at": datetime.utcnow()}}
            )
            if result.modified_count:
                await audit_service.log_event(
                    action="participant_role_changed",
                    actor_id=actor_id,
                    conversation_id=conversation_id,
                    payload={"participant_id": participant_id, "new_role": new_role},
                    correlation_id=correlation_id,
                )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error changing participant role: {str(e)}")
            return False

    async def get_participants(self, conversation_id: str) -> List[Dict[str, Any]]:
        db = await self._get_db()
        conv = await db.conversations.find_one({"_id": ObjectId(conversation_id)}, {"participants": 1})
        return conv.get("participants", []) if conv else []

    async def get_participant_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        db = await self._get_db()
        # Leverage audit logs for history
        cursor = db.audit_logs.find({
            "conversation_id": ObjectId(conversation_id),
            "action": {"$in": ["participant_added", "participant_removed", "participant_role_changed"]}
        }).sort("created_at", 1)
        return await cursor.to_list(length=500)

    # ----------------- Archiving / Soft Deletion -----------------
    async def archive_conversation(self, conversation_id: str, actor_id: Optional[str] = None, correlation_id: Optional[str] = None) -> bool:
        db = await self._get_db()
        result = await db.conversations.update_one({"_id": ObjectId(conversation_id)}, {"$set": {"is_archived": True, "archived_at": datetime.utcnow(), "updated_at": datetime.utcnow()}})
        if result.modified_count:
            await audit_service.log_event(
                action="conversation_archived",
                actor_id=actor_id,
                conversation_id=conversation_id,
                correlation_id=correlation_id,
            )
        return result.modified_count > 0

    async def restore_conversation(self, conversation_id: str, actor_id: Optional[str] = None, correlation_id: Optional[str] = None) -> bool:
        db = await self._get_db()
        result = await db.conversations.update_one({"_id": ObjectId(conversation_id)}, {"$set": {"is_archived": False, "archived_at": None, "updated_at": datetime.utcnow()}})
        if result.modified_count:
            await audit_service.log_event(
                action="conversation_restored",
                actor_id=actor_id,
                conversation_id=conversation_id,
                correlation_id=correlation_id,
            )
        return result.modified_count > 0

    async def purge_conversation(self, conversation_id: str, confirm: bool, actor_id: Optional[str] = None, correlation_id: Optional[str] = None) -> bool:
        if not confirm:
            return False
        db = await self._get_db()
        conv = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
        if not conv:
            return False
        await db.messages.delete_many({"conversation_id": ObjectId(conversation_id)})
        result = await db.conversations.delete_one({"_id": ObjectId(conversation_id)})
        if result.deleted_count:
            await audit_service.log_event(
                action="conversation_purged",
                actor_id=actor_id,
                conversation_id=conversation_id,
                correlation_id=correlation_id,
            )
        return result.deleted_count > 0

    # ----------------- Conversation Assignment Management -----------------
    async def claim_conversation(
        self, 
        conversation_id: str, 
        agent_id: str, 
        actor_id: Optional[str] = None, 
        correlation_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Claim a conversation by an agent.
        
        Args:
            conversation_id: Conversation ID to claim
            agent_id: ID of the agent claiming the conversation
            actor_id: ID of the user performing the action
            correlation_id: Request correlation ID for tracing
            
        Returns:
            Updated conversation document or None if failed
        """
        try:
            db = await self._get_db()
            
            # Get current conversation
            conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found for claiming")
                return None
            
            # Check if conversation is already assigned
            if conversation.get("assigned_agent_id"):
                # If it's assigned to the same agent, just return the conversation
                if str(conversation["assigned_agent_id"]) == agent_id:
                    logger.info(f"Conversation {conversation_id} is already assigned to the requesting agent {agent_id}")
                    return conversation
                else:
                    logger.warning(f"Conversation {conversation_id} is already assigned to {conversation['assigned_agent_id']}")
                    return None
            
            # Update conversation with assigned agent
            update_data = {
                "assigned_agent_id": ObjectId(agent_id),
                "updated_at": datetime.utcnow(),
                "status": "active"  # Activate the conversation when claimed
            }
            
            result = await db.conversations.update_one(
                {"_id": ObjectId(conversation_id)},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                logger.warning(f"Failed to update conversation {conversation_id} for claiming")
                return None
            
            # Get updated conversation
            updated_conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
            
            # Log audit event
            await audit_service.log_event(
                action="conversation_claimed",
                actor_id=actor_id,
                conversation_id=conversation_id,
                payload={
                    "agent_id": agent_id,
                    "previous_agent_id": None,
                    "claim_method": "manual"
                },
                correlation_id=correlation_id,
            )
            
            logger.info(f"Conversation {conversation_id} claimed by agent {agent_id}")
            return updated_conversation
            
        except Exception as e:
            logger.error(f"Error claiming conversation {conversation_id}: {str(e)}")
            return None

    async def auto_assign_conversation(
        self, 
        conversation_id: str, 
        agent_id: str, 
        actor_id: Optional[str] = None, 
        correlation_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Automatically assign a conversation to an agent (e.g., when they send first message).
        
        Args:
            conversation_id: Conversation ID to assign
            agent_id: ID of the agent being assigned
            actor_id: ID of the user performing the action
            correlation_id: Request correlation ID for tracing
            
        Returns:
            Updated conversation document or None if failed
        """
        try:
            db = await self._get_db()
            
            # Get current conversation
            conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found for auto-assignment")
                return None
            
            # Check if conversation is already assigned
            if conversation.get("assigned_agent_id"):
                logger.info(f"Conversation {conversation_id} is already assigned to {conversation['assigned_agent_id']}")
                return conversation
            
            # Update conversation with assigned agent
            update_data = {
                "assigned_agent_id": ObjectId(agent_id),
                "updated_at": datetime.utcnow(),
                "status": "active"  # Activate the conversation when assigned
            }
            
            result = await db.conversations.update_one(
                {"_id": ObjectId(conversation_id)},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                logger.warning(f"Failed to update conversation {conversation_id} for auto-assignment")
                return None
            
            # Get updated conversation
            updated_conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
            
            # Log audit event
            await audit_service.log_event(
                action="conversation_auto_assigned",
                actor_id=actor_id,
                conversation_id=conversation_id,
                payload={
                    "agent_id": agent_id,
                    "previous_agent_id": None,
                    "claim_method": "auto"
                },
                correlation_id=correlation_id,
            )
            
            logger.info(f"Conversation {conversation_id} auto-assigned to agent {agent_id}")
            return updated_conversation
            
        except Exception as e:
            logger.error(f"Error auto-assigning conversation {conversation_id}: {str(e)}")
            return None

    async def get_conversation_stats(self) -> Dict[str, Any]:
        """
        Get conversation statistics for dashboard.
        
        Returns:
            Dictionary containing conversation statistics
        """
        try:
            db = await self._get_db()
            
            # Get conversation counts
            total_conversations = await db.conversations.count_documents({})
            active_conversations = await db.conversations.count_documents({"status": "active"})
            closed_conversations = await db.conversations.count_documents({"status": "closed"})
            unassigned_conversations = await db.conversations.count_documents({"assigned_agent_id": None})
            
            # Get conversations by status
            status_pipeline = [
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]
            status_stats = await db.conversations.aggregate(status_pipeline).to_list(None)
            conversations_by_status = {str(item["_id"]) if item["_id"] is not None else "unknown": item["count"] for item in status_stats}
            
            # Get conversations by priority
            priority_pipeline = [
                {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
            ]
            priority_stats = await db.conversations.aggregate(priority_pipeline).to_list(None)
            conversations_by_priority = {str(item["_id"]) if item["_id"] is not None else "unknown": item["count"] for item in priority_stats}
            
            # Get conversations by channel
            channel_pipeline = [
                {"$group": {"_id": "$channel", "count": {"$sum": 1}}}
            ]
            channel_stats = await db.conversations.aggregate(channel_pipeline).to_list(None)
            conversations_by_channel = {str(item["_id"]) if item["_id"] is not None else "unknown": item["count"] for item in channel_stats}
            
            stats = {
                "total_conversations": total_conversations,
                "active_conversations": active_conversations,
                "closed_conversations": closed_conversations,
                "unassigned_conversations": unassigned_conversations,
                "conversations_by_status": conversations_by_status,
                "conversations_by_priority": conversations_by_priority,
                "conversations_by_channel": conversations_by_channel,
                "average_response_time_minutes": 0.0,  # TODO: Calculate from messages
                "average_resolution_time_minutes": 0.0,  # TODO: Calculate from closed conversations
                "customer_satisfaction_rate": 0.0  # TODO: Calculate from surveys
            }
            
            logger.info(f"📊 [STATS] Generated conversation stats: {total_conversations} total, {active_conversations} active")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting conversation stats: {str(e)}")
            # Return empty stats on error
            return {
                "total_conversations": 0,
                "active_conversations": 0,
                "closed_conversations": 0,
                "unassigned_conversations": 0,
                "conversations_by_status": {},
                "conversations_by_priority": {},
                "conversations_by_channel": {},
                "average_response_time_minutes": 0.0,
                "average_resolution_time_minutes": 0.0,
                "customer_satisfaction_rate": 0.0
            }


# Global conversation service instance
conversation_service = ConversationService() 