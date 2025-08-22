"""
Conversation summarizer service.
Main service for generating conversation summaries using LangChain.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.logger import logger
from app.services.ai.agents.conversation_summarizer.chains.summarization_chains import SummarizationChains
from app.services.ai.agents.conversation_summarizer.schemas import (
    ConversationSummaryRequest,
    ConversationSummaryResponse,
    ConversationData,
    MessageData,
    SummarizationConfig,
    SummarizationResult
)
from app.services.ai.shared.base_tools import validate_conversation_id
from app.services import conversation_service, cursor_message_service


class ConversationSummarizerService:
    """
    Service for generating conversation summaries using AI.
    """
    
    def __init__(self):
        """Initialize the summarizer service."""
        self.chains = SummarizationChains()
        self._cache: Dict[str, ConversationSummaryResponse] = {}
        self._cache_ttl = 3600  # 1 hour cache TTL
    
    async def summarize_conversation(
        self,
        request: ConversationSummaryRequest
    ) -> SummarizationResult:
        """
        Generate a summary for a conversation.
        
        Args:
            request: Summarization request
            
        Returns:
            SummarizationResult with the generated summary
        """
        try:
            # Validate conversation ID
            if not validate_conversation_id(request.conversation_id):
                return SummarizationResult(
                    success=False,
                    error="Invalid conversation ID format",
                    processing_time=0.0
                )
            
            # Check cache first
            cache_key = f"{request.conversation_id}_{request.summary_type}"
            cached_summary = self._get_cached_summary(cache_key)
            if cached_summary:
                logger.info(f"Returning cached summary for conversation {request.conversation_id}")
                return SummarizationResult(
                    success=True,
                    summary=cached_summary,
                    processing_time=0.0
                )
            
            # Load conversation data
            conversation_data = await self._load_conversation_data(request.conversation_id)
            if not conversation_data:
                return SummarizationResult(
                    success=False,
                    error="Conversation not found or no messages available",
                    processing_time=0.0
                )
            
            # Create summarization config
            config = SummarizationConfig(
                max_summary_length=500,
                include_key_points=True,
                include_sentiment=True,
                include_topics=True,
                language="auto",
                style="professional"
            )
            
            # Generate summary
            result = await self.chains.generate_summary(conversation_data, config)
            
            # Cache successful results
            if result.success and result.summary:
                self._cache_summary(cache_key, result.summary)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in summarize_conversation: {str(e)}")
            return SummarizationResult(
                success=False,
                error=f"Summarization failed: {str(e)}",
                processing_time=0.0
            )
    
    async def _load_conversation_data(self, conversation_id: str) -> Optional[ConversationData]:
        """
        Load conversation data from database.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            ConversationData or None if not found
        """
        try:
            # Load conversation
            conversation = await conversation_service.get_conversation(conversation_id)
            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found")
                return None
            
            # Load messages using cursor service
            messages_result = await cursor_message_service.get_messages_cursor(
                conversation_id=conversation_id,
                limit=1000  # Limit to prevent memory issues
            )
            
            messages = messages_result.get("messages", [])
            
            if not messages:
                logger.warning(f"No messages found for conversation {conversation_id}")
                return None
            
            # Convert to MessageData objects
            message_data_list = []
            for msg in messages:
                # Map the message fields correctly
                content = msg.get("text_content", "") or msg.get("content", "")
                role = msg.get("sender_role", "user")
                timestamp = msg.get("timestamp", datetime.now())
                message_type = msg.get("type", "text")
                
                message_data = MessageData(
                    message_id=str(msg.get("_id")),
                    content=content,
                    role=role,
                    timestamp=timestamp,
                    message_type=message_type,
                    metadata=msg.get("metadata", {})
                )
                message_data_list.append(message_data)
            
            # Determine conversation start and end times
            start_time = None
            end_time = None
            if message_data_list:
                sorted_messages = sorted(message_data_list, key=lambda x: x.timestamp)
                start_time = sorted_messages[0].timestamp
                end_time = sorted_messages[-1].timestamp
            
            # Create conversation data
            conversation_data = ConversationData(
                conversation_id=conversation_id,
                messages=message_data_list,
                participants=conversation.get("participants", []),
                start_time=start_time,
                end_time=end_time,
                metadata=conversation.get("metadata", {})
            )
            
            logger.info(f"Loaded {len(message_data_list)} messages for conversation {conversation_id}")
            return conversation_data
            
        except Exception as e:
            logger.error(f"Error loading conversation data: {str(e)}")
            return None
    
    def _get_cached_summary(self, cache_key: str) -> Optional[ConversationSummaryResponse]:
        """
        Get cached summary if available and not expired.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached summary or None
        """
        if cache_key in self._cache:
            cached_summary = self._cache[cache_key]
            
            # Check if cache is still valid
            age = (datetime.now() - cached_summary.generated_at).total_seconds()
            if age < self._cache_ttl:
                return cached_summary
            else:
                # Remove expired cache entry
                del self._cache[cache_key]
        
        return None
    
    def _cache_summary(self, cache_key: str, summary: ConversationSummaryResponse):
        """
        Cache a summary.
        
        Args:
            cache_key: Cache key
            summary: Summary to cache
        """
        # Limit cache size
        if len(self._cache) >= 100:
            # Remove oldest entries
            oldest_keys = sorted(
                self._cache.keys(),
                key=lambda k: self._cache[k].generated_at
            )[:20]
            for key in oldest_keys:
                del self._cache[key]
        
        self._cache[cache_key] = summary
        logger.debug(f"Cached summary for key: {cache_key}")
    
    async def clear_cache(self, conversation_id: Optional[str] = None):
        """
        Clear summary cache.
        
        Args:
            conversation_id: Specific conversation to clear, or None for all
        """
        if conversation_id:
            # Clear specific conversation cache
            keys_to_remove = [
                key for key in self._cache.keys()
                if key.startswith(f"{conversation_id}_")
            ]
            for key in keys_to_remove:
                del self._cache[key]
            logger.info(f"Cleared cache for conversation {conversation_id}")
        else:
            # Clear all cache
            self._cache.clear()
            logger.info("Cleared all summary cache")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics
        """
        total_entries = len(self._cache)
        total_size = sum(
            len(str(summary.summary)) for summary in self._cache.values()
        )
        
        return {
            "total_entries": total_entries,
            "total_size_bytes": total_size,
            "cache_ttl_seconds": self._cache_ttl
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the summarizer service.
        
        Returns:
            Health check results
        """
        try:
            # Test LLM connection
            test_result = await self.chains.summary_chain.ainvoke({
                "conversation_text": "Test message",
                "summary_style": "professional",
                "max_length": 100
            })
            
            cache_stats = await self.get_cache_stats()
            
            return {
                "status": "healthy",
                "llm_connection": "ok",
                "cache_stats": cache_stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Summarizer health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Global instance
summarizer_service = ConversationSummarizerService()
