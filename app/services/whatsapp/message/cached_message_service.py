"""Cached Message Service with Redis optimization for fast chat loading."""

from typing import Dict, List, Optional, Any, Tuple
from bson import ObjectId
from datetime import datetime, timezone

from app.services.base_service import BaseService
from app.services.cache.redis_service import redis_service
from app.core.logger import logger


class CachedMessageService(BaseService):
    """Service for optimized message loading with Redis caching."""
    
    def __init__(self):
        super().__init__()
    
    async def get_message_window(
        self,
        user_id: str,
        conversation_id: str,
        anchor: str = "latest",
        direction: str = "before", 
        limit: int = 50,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get a window of messages with Redis caching and cursor-based pagination.
        
        Args:
            user_id: User ID for cache key and permissions
            conversation_id: Conversation ID
            anchor: Message ID to start from or "latest" for most recent
            direction: "before" (older) or "after" (newer)
            limit: Number of messages to return (max 100)
            use_cache: Whether to use Redis cache
            
        Returns:
            {
                "messages": [...],
                "has_more": bool,
                "next_cursor": str or None,
                "prev_cursor": str or None,
                "cache_hit": bool
            }
        """
        limit = min(limit, 100)  # Enforce max limit
        cache_hit = False
        
        try:
            # Try to get from cache first
            if use_cache:
                cached_window = await redis_service.get_cached_message_window(
                    user_id, conversation_id, anchor, direction, limit
                )
                if cached_window:
                    cache_hit = True
                    messages = cached_window["messages"]
                    return {
                        "messages": messages,
                        "has_more": len(messages) == limit,
                        "next_cursor": self._get_next_cursor(messages, direction),
                        "prev_cursor": self._get_prev_cursor(messages, direction),
                        "cache_hit": True
                    }
            
            # Cache miss - fetch from database
            logger.info(f"📂 [CACHED_MSG] Fetching from DB: {conversation_id}, anchor: {anchor}, direction: {direction}, limit: {limit}")
            
            db = await self._get_db()
            
            # Build query based on anchor and direction
            query = {"conversation_id": ObjectId(conversation_id)}
            
            if anchor != "latest":
                anchor_message = await db.messages.find_one({"_id": ObjectId(anchor)})
                if anchor_message:
                    if direction == "before":
                        # Get messages older than anchor
                        query["timestamp"] = {"$lt": anchor_message["timestamp"]}
                    else:
                        # Get messages newer than anchor
                        query["timestamp"] = {"$gt": anchor_message["timestamp"]}
            
            # Execute query with optimized sorting
            cursor = db.messages.find(query)
            
            if direction == "before":
                # For older messages, sort descending and reverse later
                cursor = cursor.sort("timestamp", -1)
            else:
                # For newer messages, sort ascending
                cursor = cursor.sort("timestamp", 1)
            
            cursor = cursor.limit(limit + 1)  # Get one extra to check if there are more
            
            messages = await cursor.to_list(length=limit + 1)
            
            # Check if there are more messages
            has_more = len(messages) > limit
            if has_more:
                messages = messages[:limit]
            
            # For "before" direction, reverse to get chronological order
            if direction == "before":
                messages.reverse()
            
            # Convert ObjectIds to strings for JSON serialization
            serialized_messages = []
            for msg in messages:
                msg_dict = dict(msg)
                msg_dict["_id"] = str(msg_dict["_id"])
                msg_dict["conversation_id"] = str(msg_dict["conversation_id"])
                if "sender_id" in msg_dict and msg_dict["sender_id"]:
                    msg_dict["sender_id"] = str(msg_dict["sender_id"])
                if "reply_to_message_id" in msg_dict and msg_dict["reply_to_message_id"]:
                    msg_dict["reply_to_message_id"] = str(msg_dict["reply_to_message_id"])
                serialized_messages.append(msg_dict)
            
            # Cache the result with shorter TTL for better freshness
            if use_cache and serialized_messages:
                await redis_service.cache_message_window(
                    user_id, conversation_id, serialized_messages, anchor, direction, limit,
                    ttl_seconds=90  # 1.5 minutes TTL for better freshness
                )
            
            next_cursor = self._get_next_cursor(serialized_messages, direction)
            prev_cursor = self._get_prev_cursor(serialized_messages, direction)
            
            logger.info(f"✅ [CACHED_MSG] Fetched {len(serialized_messages)} messages from DB")
            
            return {
                "messages": serialized_messages,
                "has_more": has_more,
                "next_cursor": next_cursor,
                "prev_cursor": prev_cursor,
                "cache_hit": cache_hit
            }
            
        except Exception as e:
            logger.error(f"❌ [CACHED_MSG] Error getting message window: {str(e)}")
            return {
                "messages": [],
                "has_more": False,
                "next_cursor": None,
                "prev_cursor": None,
                "cache_hit": False
            }
    
    def _get_next_cursor(self, messages: List[Dict[str, Any]], direction: str) -> Optional[str]:
        """Get the next cursor for pagination."""
        if not messages:
            return None
        
        if direction == "before":
            # For older messages, cursor is the oldest message ID
            return messages[0]["_id"]
        else:
            # For newer messages, cursor is the newest message ID
            return messages[-1]["_id"]
    
    def _get_prev_cursor(self, messages: List[Dict[str, Any]], direction: str) -> Optional[str]:
        """Get the previous cursor for pagination."""
        if not messages:
            return None
        
        if direction == "before":
            # For older messages, prev cursor is the newest message ID
            return messages[-1]["_id"]
        else:
            # For newer messages, prev cursor is the oldest message ID
            return messages[0]["_id"]
    
    async def get_recent_messages_optimized(
        self,
        user_id: str,
        conversation_id: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get recent messages with optimized caching for chat entry.
        This is the main method for opening a chat quickly.
        """
        return await self.get_message_window(
            user_id=user_id,
            conversation_id=conversation_id,
            anchor="latest",
            direction="before",
            limit=limit,
            use_cache=True
        )
    
    async def get_older_messages(
        self,
        user_id: str,
        conversation_id: str,
        cursor: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get older messages for scroll-up lazy loading.
        """
        return await self.get_message_window(
            user_id=user_id,
            conversation_id=conversation_id,
            anchor=cursor,
            direction="before",
            limit=limit,
            use_cache=True
        )
    
    async def get_newer_messages(
        self,
        user_id: str,
        conversation_id: str,
        cursor: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get newer messages for real-time updates.
        """
        return await self.get_message_window(
            user_id=user_id,
            conversation_id=conversation_id,
            anchor=cursor,
            direction="after",
            limit=limit,
            use_cache=True
        )
    
    async def invalidate_conversation_cache(
        self,
        conversation_id: str,
        user_ids: Optional[List[str]] = None
    ):
        """
        Invalidate cached messages for a conversation.
        Call this when new messages arrive or messages are modified.
        """
        await redis_service.invalidate_conversation_cache(conversation_id, user_ids)
    
    async def get_conversation_with_cached_messages(
        self,
        conversation_id: str,
        user_id: str,
        is_super_admin: bool = False,
        messages_limit: int = 50
    ) -> Optional[Dict[str, Any]]:
        """
        Get conversation with recent messages using cache.
        This replaces the original get_conversation_with_messages for better performance.
        """
        try:
            db = await self._get_db()
            
            # Get conversation metadata (try cache first)
            cached_metadata = await redis_service.get_cached_conversation_metadata(conversation_id)
            
            if cached_metadata:
                conversation = cached_metadata
                logger.info(f"🔴 [CACHED_MSG] Using cached conversation metadata")
            else:
                # Fetch from database
                conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
                if not conversation:
                    return None
                
                # Cache the conversation metadata
                conv_dict = dict(conversation)
                conv_dict["_id"] = str(conv_dict["_id"])
                if "assigned_agent_id" in conv_dict and conv_dict["assigned_agent_id"]:
                    conv_dict["assigned_agent_id"] = str(conv_dict["assigned_agent_id"])
                if "department_id" in conv_dict and conv_dict["department_id"]:
                    conv_dict["department_id"] = str(conv_dict["department_id"])
                if "created_by" in conv_dict and conv_dict["created_by"]:
                    conv_dict["created_by"] = str(conv_dict["created_by"])
                
                await redis_service.cache_conversation_metadata(conversation_id, conv_dict)
                conversation = conv_dict
            
            # Check access permissions
            has_access = is_super_admin
            if not has_access:
                user_obj_id = ObjectId(user_id)
                conv_assigned_id = conversation.get("assigned_agent_id")
                conv_created_by = conversation.get("created_by")
                
                # Convert string IDs back to ObjectId for comparison
                if isinstance(conv_assigned_id, str):
                    conv_assigned_id = ObjectId(conv_assigned_id)
                if isinstance(conv_created_by, str):
                    conv_created_by = ObjectId(conv_created_by)
                
                has_access = (
                    conv_assigned_id == user_obj_id or
                    conv_created_by == user_obj_id
                )
            
            if not has_access:
                return {
                    "conversation": conversation,
                    "messages": [],
                    "messages_total": 0,
                    "initial_unread_count": 0,
                    "has_access": False,
                    "cache_hit": False
                }
            
            # Get recent messages using cache
            message_result = await self.get_recent_messages_optimized(
                user_id=user_id,
                conversation_id=conversation_id,
                limit=messages_limit
            )
            
            messages = message_result["messages"]
            cache_hit = message_result["cache_hit"]
            
            # Get total message count (this could also be cached)
            total_count = await db.messages.count_documents({"conversation_id": ObjectId(conversation_id)})
            
            # Calculate initial unread count using the cache from conversation service
            from app.services import conversation_service
            
            # Check if we have cached initial unread count
            if user_id not in conversation_service._initial_unread_cache:
                conversation_service._initial_unread_cache[user_id] = {}
            
            if conversation_id not in conversation_service._initial_unread_cache[user_id]:
                # First time accessing - calculate and cache
                current_unread_count = await db.messages.count_documents({
                    "conversation_id": ObjectId(conversation_id),
                    "direction": "inbound",
                    "status": {"$ne": "read"},
                    "sender_role": "customer"
                })
                conversation_service._initial_unread_cache[user_id][conversation_id] = current_unread_count
            
            initial_unread_count = conversation_service._initial_unread_cache[user_id][conversation_id]
            
            logger.info(f"✅ [CACHED_MSG] Retrieved conversation {conversation_id} with {len(messages)} messages (cache_hit: {cache_hit})")
            
            return {
                "conversation": conversation,
                "messages": messages,
                "messages_total": total_count,
                "initial_unread_count": initial_unread_count,
                "has_access": True,
                "cache_hit": cache_hit
            }
            
        except Exception as e:
            logger.error(f"❌ [CACHED_MSG] Error getting conversation with cached messages: {str(e)}")
            return None


# Global instance
cached_message_service = CachedMessageService()
