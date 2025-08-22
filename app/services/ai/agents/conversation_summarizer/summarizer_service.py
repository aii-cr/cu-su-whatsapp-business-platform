"""
Conversation summarizer service.
Main service for generating conversation summaries using LangChain.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId

from app.core.logger import logger
from app.services.ai.agents.conversation_summarizer.chains.summarization_chains import SummarizationChains
from app.services.ai.agents.conversation_summarizer.schemas import (
    ConversationSummaryRequest,
    ConversationSummaryResponse,
    ConversationData,
    MessageData,
    SummarizationConfig,
    SummarizationResult,
    StoredConversationSummary
)
from app.services.ai.shared.base_tools import validate_conversation_id
from app.services import conversation_service, cursor_message_service, audit_service
from app.services.base_service import BaseService


class ConversationSummarizerService(BaseService):
    """
    Service for generating conversation summaries using AI.
    """
    
    def __init__(self):
        """Initialize the summarizer service."""
        super().__init__()
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
            
            if result.success and result.summary:
                # Set the user who generated the summary
                result.summary.generated_by = request.user_id
                
                # Store summary in MongoDB
                await self._store_summary(request.conversation_id, result.summary, request.user_id)
                
                # Log audit event
                await self._log_summary_generation(request.conversation_id, request.user_id, result.summary)
                
                # Cache successful results
                self._cache_summary(cache_key, result.summary)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in summarize_conversation: {str(e)}")
            return SummarizationResult(
                success=False,
                error=f"Summarization failed: {str(e)}",
                processing_time=0.0
            )
    
    async def get_stored_summary(self, conversation_id: str) -> Optional[ConversationSummaryResponse]:
        """
        Get stored summary from MongoDB.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Stored summary or None
        """
        try:
            db = await self._get_db()
            
            # Get the latest summary for this conversation
            stored_summary = await db.conversation_summaries.find_one(
                {"conversation_id": conversation_id},
                sort=[("created_at", -1)]
            )
            
            if stored_summary:
                # Convert to response format
                summary_data = stored_summary.get("summary_data", {})
                return ConversationSummaryResponse(**summary_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting stored summary: {str(e)}")
            return None
    
    async def _store_summary(
        self, 
        conversation_id: str, 
        summary: ConversationSummaryResponse, 
        user_id: Optional[str] = None
    ):
        """
        Store summary in MongoDB.
        
        Args:
            conversation_id: Conversation ID
            summary: Summary to store
            user_id: User who generated the summary
        """
        try:
            db = await self._get_db()
            
            # Get current version
            current_summary = await db.conversation_summaries.find_one(
                {"conversation_id": conversation_id},
                sort=[("version", -1)]
            )
            
            version = 1
            if current_summary:
                version = current_summary.get("version", 0) + 1
            
            # Create stored summary document
            stored_summary = StoredConversationSummary(
                conversation_id=conversation_id,
                summary_data=summary,
                created_by=user_id,
                version=version
            )
            
            # Insert into database
            await db.conversation_summaries.insert_one(stored_summary.model_dump())
            
            logger.info(f"Stored summary version {version} for conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"Error storing summary: {str(e)}")
    
    async def _log_summary_generation(
        self, 
        conversation_id: str, 
        user_id: Optional[str], 
        summary: ConversationSummaryResponse
    ):
        """
        Log summary generation in audit service.
        
        Args:
            conversation_id: Conversation ID
            user_id: User who generated the summary
            summary: Generated summary
        """
        try:
            await audit_service.log_event(
                action="conversation_summary_generated",
                actor_id=user_id,
                conversation_id=conversation_id,
                payload={
                    "summary_length": len(summary.summary),
                    "message_count": summary.message_count,
                    "ai_message_count": summary.ai_message_count,
                    "sentiment": summary.sentiment,
                    "sentiment_emoji": summary.sentiment_emoji,
                    "key_points_count": len(summary.key_points),
                    "topics_count": len(summary.topics),
                    "human_agents_count": len(summary.human_agents)
                }
            )
            
            logger.info(f"Logged summary generation for conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"Error logging summary generation: {str(e)}")
    
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
            
            # Extract human agents from messages
            human_agents = self._extract_human_agents(messages)
            
            # Convert to MessageData objects
            message_data_list = []
            for msg in messages:
                # Map the message fields correctly
                content = msg.get("text_content", "") or msg.get("content", "")
                role = msg.get("sender_role", "user")
                timestamp = msg.get("timestamp", datetime.now())
                message_type = msg.get("type", "text")
                sender_name = msg.get("sender_name")
                sender_email = msg.get("sender_email")
                
                message_data = MessageData(
                    message_id=str(msg.get("_id")),
                    content=content,
                    role=role,
                    sender_name=sender_name,
                    sender_email=sender_email,
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
                human_agents=human_agents,
                start_time=start_time,
                end_time=end_time,
                metadata=conversation.get("metadata", {})
            )
            
            logger.info(f"Loaded {len(message_data_list)} messages for conversation {conversation_id}")
            return conversation_data
            
        except Exception as e:
            logger.error(f"Error loading conversation data: {str(e)}")
            return None
    
    def _extract_human_agents(self, messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Extract human agents from messages.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            List of human agents with name and email
        """
        human_agents = {}
        
        for msg in messages:
            role = msg.get("sender_role", "user")
            
            # Only include human agents (not AI assistant or customer)
            if role not in ["assistant", "user"]:
                sender_name = msg.get("sender_name")
                sender_email = msg.get("sender_email")
                
                if sender_name and sender_name not in human_agents:
                    human_agents[sender_name] = {
                        "name": sender_name,
                        "email": sender_email or "No email"
                    }
        
        return list(human_agents.values())
    
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
