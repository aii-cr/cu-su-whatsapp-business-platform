"""Cursor-based message service with Redis caching for efficient pagination."""

import hashlib
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from bson import ObjectId

from app.services.base_service import BaseService
from app.core.logger import logger
from app.services.cache.redis_service import redis_service
from app.config.error_codes import ErrorCode


class CursorMessageService(BaseService):
    """Service for cursor-based message pagination with Redis caching."""
    
    def __init__(self):
        super().__init__()
    

    
    async def get_messages_cursor(
        self,
        conversation_id: str,
        limit: int,
        before: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get messages with cursor-based pagination.
        
        Args:
            conversation_id: Conversation ID
            limit: Number of messages to return
            before: Cursor for pagination (ObjectId)
            user_id: User ID for cache key (optional)
            
        Returns:
            Dict with messages, next_cursor, has_more, and cache_hit
        """
        db = await self._get_db()
        
        try:
            # Try cache first for latest messages (no before cursor)
            cache_hit = False
            if not before:
                # Use the existing Redis service method for caching
                cached_data = await redis_service.get_cached_message_window(
                    user_id=user_id or "system",
                    conversation_id=conversation_id,
                    anchor="latest",
                    direction="before",
                    limit=limit
                )
                if cached_data:
                    logger.info(f"🔴 [CACHE] Cache hit for conversation {conversation_id}")
                    return {
                        "messages": cached_data.get("messages", []),
                        "next_cursor": cached_data.get("next_cursor"),
                        "has_more": cached_data.get("has_more", False),
                        "cache_hit": True,
                        "etag": cached_data.get("etag")
                    }
            
            # Build query filter
            query_filter = {"conversation_id": ObjectId(conversation_id)}
            
            # Add cursor filter if provided
            if before:
                query_filter["_id"] = {"$lt": ObjectId(before)}
            
            # Execute query with cursor-based pagination
            cursor = db.messages.find(query_filter).sort("_id", -1).limit(limit + 1)
            messages = await cursor.to_list(length=limit + 1)
            
            # Check if there are more messages
            has_more = len(messages) > limit
            if has_more:
                messages = messages[:-1]  # Remove the extra message
            
            # Convert ObjectIds to strings
            for message in messages:
                message["_id"] = str(message["_id"])
                message["conversation_id"] = str(message["conversation_id"])
                if message.get("sender_id"):
                    message["sender_id"] = str(message["sender_id"])
                if message.get("reply_to_message_id"):
                    message["reply_to_message_id"] = str(message["reply_to_message_id"])
                if message.get("media_id"):
                    message["media_id"] = str(message["media_id"])
            
            # Determine next cursor
            next_cursor = None
            if messages and has_more:
                next_cursor = messages[-1]["_id"]
            
            result = {
                "messages": messages,
                "next_cursor": next_cursor,
                "has_more": has_more,
                "cache_hit": cache_hit
            }
            
            # Cache the result for latest messages (no before cursor)
            if not before and messages:
                try:
                    await redis_service.cache_message_window(
                        user_id=user_id or "system",
                        conversation_id=conversation_id,
                        messages=messages,
                        anchor="latest",
                        direction="before",
                        limit=limit,
                        ttl_seconds=60
                    )
                    logger.info(f"🔴 [CACHE] Cached messages for conversation {conversation_id}")
                except Exception as e:
                    logger.warning(f"🔴 [CACHE] Failed to cache messages for {conversation_id}: {str(e)}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ [CURSOR_SERVICE] Error getting messages for conversation {conversation_id}: {str(e)}")
            raise
    
    async def get_messages_around(
        self,
        conversation_id: str,
        anchor_id: str,
        limit: int,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get messages around a specific message ID.
        
        Args:
            conversation_id: Conversation ID
            anchor_id: Message ID to center around
            limit: Number of messages to return
            user_id: User ID (optional)
            
        Returns:
            Dict with messages, next_cursor, and has_more
        """
        db = await self._get_db()
        
        try:
            # First, get the anchor message to verify it exists
            anchor_message = await db.messages.find_one({
                "_id": ObjectId(anchor_id),
                "conversation_id": ObjectId(conversation_id)
            })
            
            if not anchor_message:
                raise ValueError(f"Anchor message {anchor_id} not found in conversation {conversation_id}")
            
            # Calculate how many messages to get before and after
            half_limit = limit // 2
            before_limit = half_limit
            after_limit = limit - half_limit
            
            # Get messages before the anchor
            before_cursor = db.messages.find({
                "conversation_id": ObjectId(conversation_id),
                "_id": {"$lt": ObjectId(anchor_id)}
            }).sort("_id", -1).limit(before_limit)
            
            before_messages = await before_cursor.to_list(length=before_limit)
            
            # Get messages after the anchor (including the anchor)
            after_cursor = db.messages.find({
                "conversation_id": ObjectId(conversation_id),
                "_id": {"$gte": ObjectId(anchor_id)}
            }).sort("_id", -1).limit(after_limit + 1)  # +1 to check if there are more
            
            after_messages = await after_cursor.to_list(length=after_limit + 1)
            
            # Check if there are more messages after
            has_more_after = len(after_messages) > after_limit
            if has_more_after:
                after_messages = after_messages[:-1]  # Remove the extra message
            
            # Combine messages (before messages are already in reverse order)
            all_messages = before_messages + after_messages
            
            # Convert ObjectIds to strings
            for message in all_messages:
                message["_id"] = str(message["_id"])
                message["conversation_id"] = str(message["conversation_id"])
                if message.get("sender_id"):
                    message["sender_id"] = str(message["sender_id"])
                if message.get("reply_to_message_id"):
                    message["reply_to_message_id"] = str(message["reply_to_message_id"])
                if message.get("media_id"):
                    message["media_id"] = str(message["media_id"])
            
            # Determine next cursor
            next_cursor = None
            if all_messages and has_more_after:
                next_cursor = all_messages[-1]["_id"]
            
            return {
                "messages": all_messages,
                "next_cursor": next_cursor,
                "has_more": has_more_after,
                "cache_hit": False  # Around queries are not cached
            }
            
        except Exception as e:
            logger.error(f"❌ [CURSOR_SERVICE] Error getting messages around {anchor_id}: {str(e)}")
            raise
    
    async def invalidate_conversation_cache(self, conversation_id: str) -> None:
        """
        Invalidate Redis cache for a conversation.
        
        Args:
            conversation_id: Conversation ID to invalidate
        """
        try:
            # Use the existing Redis service method for cache invalidation
            await redis_service.invalidate_conversation_cache(conversation_id)
            logger.info(f"🔴 [CACHE] Invalidated cache for conversation {conversation_id}")
        except Exception as e:
            logger.warning(f"🔴 [CACHE] Failed to invalidate cache for {conversation_id}: {str(e)}")


# Global instance
cursor_message_service = CursorMessageService()
