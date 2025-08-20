"""Redis Cache Service for optimizing message loading performance."""

import json
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import timedelta
import redis.asyncio as redis
from bson import ObjectId

from app.core.config import settings
from app.core.logger import logger


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle ObjectId and other MongoDB types."""
    
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        elif hasattr(obj, 'isoformat'):  # Handle datetime objects
            return obj.isoformat()
        return super().default(obj)


class RedisService:
    """Service for Redis caching operations."""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self._lock = asyncio.Lock()
        
    async def connect(self):
        """Connect to Redis."""
        if self.redis is None:
            async with self._lock:
                if self.redis is None:
                    try:
                        redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379')
                        self.redis = redis.from_url(
                            redis_url,
                            decode_responses=True,
                            encoding='utf-8'
                        )
                        await self.redis.ping()
                        logger.info("🔴 [REDIS] Connected successfully")
                    except Exception as e:
                        logger.error(f"❌ [REDIS] Connection failed: {str(e)}")
                        self.redis = None
                        raise
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            self.redis = None
            logger.info("🔴 [REDIS] Disconnected")
    
    async def _ensure_connected(self):
        """Ensure Redis connection is established."""
        if self.redis is None:
            await self.connect()
    
    # ==================== MESSAGE CACHE OPERATIONS ====================
    
    def _get_message_window_key(self, user_id: str, conversation_id: str, anchor: str, direction: str, limit: int) -> str:
        """Generate Redis key for message window."""
        return f"u:{user_id}:conv:{conversation_id}:win:{anchor}:{direction}:{limit}"
    
    def _get_conversation_metadata_key(self, conversation_id: str) -> str:
        """Generate Redis key for conversation metadata."""
        return f"conv:{conversation_id}:meta"
    
    def _get_unread_count_key(self, user_id: str, conversation_id: str) -> str:
        """Generate Redis key for user unread count."""
        return f"u:{user_id}:conv:{conversation_id}:unread"
    
    def _get_conversation_last_message_key(self, conversation_id: str) -> str:
        """Generate Redis key for conversation's last message timestamp."""
        return f"conv:{conversation_id}:last_msg"
    
    async def cache_message_window(
        self, 
        user_id: str, 
        conversation_id: str, 
        messages: List[Dict[str, Any]], 
        anchor: str = "latest", 
        direction: str = "before", 
        limit: int = 50,
        ttl_seconds: int = 90  # Default 1.5 minutes for better freshness
    ) -> bool:
        """Cache a window of messages with optimized TTL."""
        try:
            await self._ensure_connected()
            
            key = self._get_message_window_key(user_id, conversation_id, anchor, direction, limit)
            
            # Prepare data for caching
            cache_data = {
                "messages": messages,
                "anchor": anchor,
                "direction": direction,
                "limit": limit,
                "user_id": user_id,
                "conversation_id": conversation_id,
                "cached_at": str(ObjectId()),  # Use ObjectId as timestamp
                "message_count": len(messages)
            }
            
            # Store in Redis with TTL
            serialized_data = json.dumps(cache_data, cls=JSONEncoder)
            await self.redis.setex(key, ttl_seconds, serialized_data)
            
            logger.info(f"🔴 [REDIS] Cached {len(messages)} messages for window {anchor}:{direction}:{limit} (TTL: {ttl_seconds}s)")
            return True
            
        except Exception as e:
            logger.error(f"❌ [REDIS] Failed to cache message window: {str(e)}")
            return False
    
    async def get_cached_message_window(
        self, 
        user_id: str, 
        conversation_id: str, 
        anchor: str = "latest", 
        direction: str = "before", 
        limit: int = 50
    ) -> Optional[Dict[str, Any]]:
        """Get cached message window."""
        try:
            await self._ensure_connected()
            
            key = self._get_message_window_key(user_id, conversation_id, anchor, direction, limit)
            cached_data = await self.redis.get(key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.info(f"🔴 [REDIS] Cache HIT for window {anchor}:{direction}:{limit}")
                return data
            else:
                logger.info(f"🔴 [REDIS] Cache MISS for window {anchor}:{direction}:{limit}")
                return None
                
        except Exception as e:
            logger.error(f"❌ [REDIS] Failed to get cached message window: {str(e)}")
            return None
    
    async def invalidate_conversation_cache(self, conversation_id: str, user_ids: Optional[List[str]] = None):
        """Invalidate all cached message windows for a conversation."""
        try:
            await self._ensure_connected()
            
            if user_ids:
                # Invalidate cache for specific users
                for user_id in user_ids:
                    pattern = f"u:{user_id}:conv:{conversation_id}:win:*"
                    keys = await self.redis.keys(pattern)
                    if keys:
                        await self.redis.delete(*keys)
                        logger.info(f"🔴 [REDIS] Invalidated {len(keys)} cache entries for user {user_id}")
            else:
                # Invalidate cache for all users (expensive operation - use sparingly)
                pattern = f"u:*:conv:{conversation_id}:win:*"
                keys = await self.redis.keys(pattern)
                if keys:
                    await self.redis.delete(*keys)
                    logger.info(f"🔴 [REDIS] Invalidated {len(keys)} cache entries for conversation")
                    
        except Exception as e:
            logger.error(f"❌ [REDIS] Failed to invalidate conversation cache: {str(e)}")
    
    async def invalidate_user_conversation_cache(self, user_id: str, conversation_id: str):
        """Invalidate cache for a specific user and conversation."""
        try:
            await self._ensure_connected()
            
            pattern = f"u:{user_id}:conv:{conversation_id}:win:*"
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"🔴 [REDIS] Invalidated {len(keys)} cache entries for user {user_id} in conversation {conversation_id}")
                
        except Exception as e:
            logger.error(f"❌ [REDIS] Failed to invalidate user conversation cache: {str(e)}")
    
    async def update_conversation_last_message(self, conversation_id: str, message_timestamp: str):
        """Update the last message timestamp for a conversation."""
        try:
            await self._ensure_connected()
            
            key = self._get_conversation_last_message_key(conversation_id)
            await self.redis.setex(key, 300, message_timestamp)  # 5 minutes TTL
            
            logger.info(f"🔴 [REDIS] Updated last message timestamp for conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"❌ [REDIS] Failed to update conversation last message: {str(e)}")
    
    async def get_conversation_last_message_timestamp(self, conversation_id: str) -> Optional[str]:
        """Get the last message timestamp for a conversation."""
        try:
            await self._ensure_connected()
            
            key = self._get_conversation_last_message_key(conversation_id)
            timestamp = await self.redis.get(key)
            
            return timestamp
            
        except Exception as e:
            logger.error(f"❌ [REDIS] Failed to get conversation last message timestamp: {str(e)}")
            return None
    
    # ==================== CONVERSATION METADATA CACHE ====================
    
    async def cache_conversation_metadata(
        self, 
        conversation_id: str, 
        metadata: Dict[str, Any], 
        ttl_seconds: int = 300  # 5 minutes TTL
    ) -> bool:
        """Cache conversation metadata."""
        try:
            await self._ensure_connected()
            
            key = self._get_conversation_metadata_key(conversation_id)
            serialized_data = json.dumps(metadata, cls=JSONEncoder)
            await self.redis.setex(key, ttl_seconds, serialized_data)
            
            logger.info(f"🔴 [REDIS] Cached metadata for conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ [REDIS] Failed to cache conversation metadata: {str(e)}")
            return False
    
    async def get_cached_conversation_metadata(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get cached conversation metadata."""
        try:
            await self._ensure_connected()
            
            key = self._get_conversation_metadata_key(conversation_id)
            cached_data = await self.redis.get(key)
            
            if cached_data:
                metadata = json.loads(cached_data)
                logger.info(f"🔴 [REDIS] Metadata cache HIT for conversation {conversation_id}")
                return metadata
            else:
                logger.info(f"🔴 [REDIS] Metadata cache MISS for conversation {conversation_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ [REDIS] Failed to get cached conversation metadata: {str(e)}")
            return None
    
    # ==================== UNREAD COUNT CACHE ====================
    
    async def cache_unread_count(
        self, 
        user_id: str, 
        conversation_id: str, 
        count: int, 
        ttl_seconds: int = 180  # 3 minutes TTL
    ) -> bool:
        """Cache unread count for user-conversation."""
        try:
            await self._ensure_connected()
            
            key = self._get_unread_count_key(user_id, conversation_id)
            await self.redis.setex(key, ttl_seconds, str(count))
            
            logger.info(f"🔴 [REDIS] Cached unread count {count} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ [REDIS] Failed to cache unread count: {str(e)}")
            return False
    
    async def get_cached_unread_count(self, user_id: str, conversation_id: str) -> Optional[int]:
        """Get cached unread count."""
        try:
            await self._ensure_connected()
            
            key = self._get_unread_count_key(user_id, conversation_id)
            cached_count = await self.redis.get(key)
            
            if cached_count is not None:
                count = int(cached_count)
                logger.info(f"🔴 [REDIS] Unread count cache HIT: {count}")
                return count
            else:
                logger.info(f"🔴 [REDIS] Unread count cache MISS")
                return None
                
        except Exception as e:
            logger.error(f"❌ [REDIS] Failed to get cached unread count: {str(e)}")
            return None
    
    # ==================== UTILITY METHODS ====================
    
    async def clear_user_cache(self, user_id: str):
        """Clear all cache entries for a specific user."""
        try:
            await self._ensure_connected()
            
            pattern = f"u:{user_id}:*"
            keys = await self.redis.keys(pattern)
            
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"🔴 [REDIS] Cleared {len(keys)} cache entries for user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ [REDIS] Failed to clear user cache: {str(e)}")
    
    async def invalidate_conversation_cache(self, conversation_id: str):
        """Invalidate all cache entries for a specific conversation."""
        try:
            await self._ensure_connected()
            
            # Pattern to match all conversation-related cache keys
            patterns = [
                f"u:*:conv:{conversation_id}:*",  # User-specific conversation cache
                f"conv:{conversation_id}:*",      # Conversation metadata cache
            ]
            
            all_keys = []
            for pattern in patterns:
                keys = await self.redis.keys(pattern)
                all_keys.extend(keys)
            
            if all_keys:
                await self.redis.delete(*all_keys)
                logger.info(f"🔴 [REDIS] Invalidated {len(all_keys)} cache entries for conversation {conversation_id}")
            else:
                logger.info(f"🔴 [REDIS] No cache entries found to invalidate for conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"❌ [REDIS] Failed to invalidate conversation cache: {str(e)}")
    
    async def invalidate_message_cache(self, conversation_id: str, message_id: str = None):
        """Invalidate message cache for a conversation, optionally for a specific message."""
        try:
            await self._ensure_connected()
            
            if message_id:
                # Invalidate specific message cache
                pattern = f"*:conv:{conversation_id}:*:{message_id}:*"
            else:
                # Invalidate all message cache for conversation
                pattern = f"*:conv:{conversation_id}:win:*"
            
            keys = await self.redis.keys(pattern)
            
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"🔴 [REDIS] Invalidated {len(keys)} message cache entries for conversation {conversation_id}")
            else:
                logger.info(f"🔴 [REDIS] No message cache entries found to invalidate for conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"❌ [REDIS] Failed to invalidate message cache: {str(e)}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        try:
            await self._ensure_connected()
            
            info = await self.redis.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0)
            }
            
        except Exception as e:
            logger.error(f"❌ [REDIS] Failed to get cache stats: {str(e)}")
            return {}
    
    async def get_cache_keys_by_pattern(self, pattern: str) -> List[str]:
        """Get cache keys matching a pattern."""
        try:
            await self._ensure_connected()
            return await self.redis.keys(pattern)
        except Exception as e:
            logger.error(f"❌ [REDIS] Failed to get cache keys: {str(e)}")
            return []


# Global Redis service instance
redis_service = RedisService()
