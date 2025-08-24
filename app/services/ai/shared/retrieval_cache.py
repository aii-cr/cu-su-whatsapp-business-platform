"""
Caching layer for RAG retrieval to improve performance.
Uses Redis for caching query results and connection pooling.
"""

import json
import hashlib
from typing import List, Optional, Dict, Any
from datetime import timedelta

import redis
from langchain_core.documents import Document
from app.core.config import settings
from app.core.logger import logger


class RetrievalCache:
    """Redis-based caching for RAG retrieval results."""
    
    def __init__(self):
        """Initialize Redis connection with error handling."""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("✅ [CACHE] Redis connection established successfully")
            self.enabled = True
        except Exception as e:
            logger.warning(f"⚠️ [CACHE] Redis connection failed, caching disabled: {str(e)}")
            self.enabled = False
            self.redis_client = None
    
    def _get_query_key(self, query: str, retrieval_params: Dict[str, Any] = None) -> str:
        """Generate cache key for a query."""
        # Include retrieval parameters in key for cache precision
        params_str = json.dumps(retrieval_params or {}, sort_keys=True)
        combined = f"{query}:{params_str}"
        return f"rag:query:{hashlib.md5(combined.encode()).hexdigest()}"
    
    def get_cached_results(self, query: str, retrieval_params: Dict[str, Any] = None) -> Optional[List[Document]]:
        """Get cached retrieval results."""
        if not self.enabled:
            return None
            
        try:
            cache_key = self._get_query_key(query, retrieval_params)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                documents = [
                    Document(page_content=doc['content'], metadata=doc['metadata'])
                    for doc in data['documents']
                ]
                logger.info(f"🎯 [CACHE] Cache HIT for query: '{query[:50]}...' ({len(documents)} docs)")
                return documents
            
            logger.debug(f"🎯 [CACHE] Cache MISS for query: '{query[:50]}...'")
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ [CACHE] Failed to get cached results: {str(e)}")
            return None
    
    def cache_results(
        self, 
        query: str, 
        documents: List[Document], 
        retrieval_params: Dict[str, Any] = None,
        ttl_seconds: int = 300  # 5 minutes default
    ) -> None:
        """Cache retrieval results."""
        if not self.enabled or not documents:
            return
            
        try:
            cache_key = self._get_query_key(query, retrieval_params)
            
            # Serialize documents
            serialized_docs = [
                {
                    'content': doc.page_content,
                    'metadata': doc.metadata
                }
                for doc in documents
            ]
            
            cache_data = {
                'query': query,
                'documents': serialized_docs,
                'params': retrieval_params or {}
            }
            
            self.redis_client.setex(
                cache_key, 
                ttl_seconds, 
                json.dumps(cache_data)
            )
            
            logger.info(f"💾 [CACHE] Cached {len(documents)} docs for query: '{query[:50]}...' (TTL: {ttl_seconds}s)")
            
        except Exception as e:
            logger.warning(f"⚠️ [CACHE] Failed to cache results: {str(e)}")
    
    def clear_cache(self, pattern: str = "rag:*") -> int:
        """Clear cached results matching pattern."""
        if not self.enabled:
            return 0
            
        try:
            keys = list(self.redis_client.scan_iter(match=pattern))
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"🗑️ [CACHE] Cleared {deleted} cached entries")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"❌ [CACHE] Failed to clear cache: {str(e)}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.enabled:
            return {"enabled": False}
            
        try:
            info = self.redis_client.info()
            rag_keys = len(list(self.redis_client.scan_iter(match="rag:*")))
            
            return {
                "enabled": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "rag_cached_queries": rag_keys
            }
            
        except Exception as e:
            logger.error(f"❌ [CACHE] Failed to get cache stats: {str(e)}")
            return {"enabled": True, "error": str(e)}


# Global cache instance
retrieval_cache = RetrievalCache()
