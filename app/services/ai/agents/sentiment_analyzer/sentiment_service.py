"""
Sentiment analyzer service for WhatsApp conversations.
Analyzes customer messages and provides real-time sentiment emoji indicators.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from bson import ObjectId

from app.core.logger import logger
from app.services.ai.agents.sentiment_analyzer.chains.sentiment_chains import SentimentChains
from app.services.ai.agents.sentiment_analyzer.schemas import (
    SentimentAnalysisRequest,
    SentimentAnalysisResponse,
    SentimentAnalysisResult,
    ConversationSentimentData,
    StoredConversationSentiment,
    SentimentWebSocketNotification
)
from app.services.ai.agents.sentiment_analyzer.config import sentiment_config
from app.services.ai.shared.utils import validate_conversation_id
from app.services import conversation_service, message_service, websocket_service, cursor_message_service
from app.services.base_service import BaseService


class SentimentAnalyzerService(BaseService):
    """
    Service for analyzing sentiment of customer messages and providing emoji indicators.
    """
    
    def __init__(self):
        """Initialize the sentiment analyzer service."""
        super().__init__()
        self.chains = SentimentChains()
        self._cache: Dict[str, ConversationSentimentData] = {}
        self._cache_ttl = sentiment_config.cache_duration_minutes * 60  # Convert to seconds
    
    async def analyze_message_sentiment(
        self,
        request: SentimentAnalysisRequest
    ) -> SentimentAnalysisResult:
        """
        Analyze sentiment of a customer message.
        
        Args:
            request: Sentiment analysis request
            
        Returns:
            SentimentAnalysisResult with analysis results
        """
        start_time = time.time()
        
        try:
            logger.info(f"😊 [SENTIMENT] Starting analyze_message_sentiment for conversation {request.conversation_id}")
            
            # Validate conversation ID
            if not validate_conversation_id(request.conversation_id):
                logger.warning(f"😊 [SENTIMENT] Invalid conversation ID format: {request.conversation_id}")
                return SentimentAnalysisResult(
                    success=False,
                    error="Invalid conversation ID format",
                    processing_time=0.0
                )
            
            # Check if sentiment analysis should be performed
            should_analyze = await self._should_analyze_sentiment(
                conversation_id=request.conversation_id,
                message_count=request.message_count,
                is_first_message=request.is_first_message
            )
            
            logger.info(f"😊 [SENTIMENT] Should analyze: {should_analyze}")
            
            if not should_analyze:
                logger.info(f"😊 [SENTIMENT] Skipping sentiment analysis based on configuration")
                return SentimentAnalysisResult(
                    success=False,
                    error="Sentiment analysis skipped based on configuration",
                    processing_time=0.0
                )
            
            # Validate message text
            if not self._is_valid_message_for_analysis(request.message_text):
                logger.warning(f"😊 [SENTIMENT] Message does not meet analysis criteria: {request.message_text}")
                return SentimentAnalysisResult(
                    success=False,
                    error="Message does not meet analysis criteria",
                    processing_time=0.0
                )
            
            # Load all customer messages for context
            customer_messages = await self._load_customer_messages(request.conversation_id)
            logger.info(f"😊 [SENTIMENT] Loaded {len(customer_messages)} customer messages")
            
            # Perform sentiment analysis with all customer messages context
            logger.info(f"😊 [SENTIMENT] Calling chains.analyze_sentiment")
            sentiment_response = await self.chains.analyze_sentiment(
                conversation_id=request.conversation_id,
                customer_messages=customer_messages
            )
            logger.info(f"😊 [SENTIMENT] chains.analyze_sentiment completed")
            
            # Set conversation and message IDs
            sentiment_response.conversation_id = request.conversation_id
            sentiment_response.message_id = request.message_id
            
            # Store sentiment data
            await self._store_sentiment_data(sentiment_response)
            
            # Update conversation model with sentiment data
            logger.info(f"😊 [SENTIMENT] Calling conversation_service.update_conversation_sentiment")
            updated_conversation = await conversation_service.update_conversation_sentiment(
                conversation_id=request.conversation_id,
                sentiment_emoji=sentiment_response.sentiment_emoji,
                confidence=sentiment_response.confidence
            )
            logger.info(f"😊 [SENTIMENT] conversation_service.update_conversation_sentiment completed: {updated_conversation is not None}")
            
            # Send WebSocket notification
            await self._notify_sentiment_update(sentiment_response)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            logger.info(
                f"✅ Sentiment analysis completed for conversation {request.conversation_id}: "
                f"{sentiment_response.sentiment_emoji} (confidence: {sentiment_response.confidence:.2f})"
            )
            
            return SentimentAnalysisResult(
                success=True,
                response=sentiment_response,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Error in sentiment analysis: {str(e)}")
            
            return SentimentAnalysisResult(
                success=False,
                error=str(e),
                processing_time=processing_time
            )
    
    async def get_conversation_sentiment(
        self,
        conversation_id: str
    ) -> Optional[ConversationSentimentData]:
        """
        Get current sentiment data for a conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            ConversationSentimentData or None if not found
        """
        try:
            # Check cache first
            cache_key = f"sentiment_{conversation_id}"
            cached_data = self._cache.get(cache_key)
            
            if cached_data:
                # Check if cache is still valid
                cache_age = (datetime.now(timezone.utc) - cached_data.updated_at).total_seconds()
                if cache_age < self._cache_ttl:
                    return cached_data
            
            # Load from database
            db = await self._get_db()
            sentiment_doc = await db.conversation_sentiments.find_one(
                {"conversation_id": conversation_id}
            )
            
            if sentiment_doc:
                sentiment_data = ConversationSentimentData(**sentiment_doc["sentiment_data"])
                
                # Update cache
                self._cache[cache_key] = sentiment_data
                
                return sentiment_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting conversation sentiment: {str(e)}")
            return None
    
    async def update_conversation_sentiment(
        self,
        conversation_id: str,
        sentiment_emoji: str,
        confidence: float,
        message_id: str
    ) -> bool:
        """
        Update conversation sentiment manually.
        
        Args:
            conversation_id: Conversation ID
            sentiment_emoji: New sentiment emoji
            confidence: Confidence score
            message_id: Message ID that triggered the update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create sentiment response
            sentiment_response = SentimentAnalysisResponse(
                conversation_id=conversation_id,
                message_id=message_id,
                sentiment_type="neutral",  # Will be determined by emoji
                sentiment_emoji=sentiment_emoji,
                confidence=confidence,
                reasoning="Manual update",
                language="auto",
                processing_time_ms=0.0
            )
            
            # Store sentiment data
            await self._store_sentiment_data(sentiment_response)
            
            # Update conversation model with sentiment data
            await conversation_service.update_conversation_sentiment(
                conversation_id=conversation_id,
                sentiment_emoji=sentiment_emoji,
                confidence=confidence
            )
            
            # Send WebSocket notification
            await self._notify_sentiment_update(sentiment_response)
            
            logger.info(f"✅ Manual sentiment update for conversation {conversation_id}: {sentiment_emoji}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating conversation sentiment: {str(e)}")
            return False
    
    async def _should_analyze_sentiment(
        self,
        conversation_id: str,
        message_count: int,
        is_first_message: bool
    ) -> bool:
        """
        Determine if sentiment analysis should be performed.
        
        Flow:
        1. First message or first reply: Always analyze
        2. Every 3rd message: Analyze (3, 6, 9, 12, etc.)
        
        Args:
            conversation_id: Conversation ID
            message_count: Current message count
            is_first_message: Whether this is the first message
            
        Returns:
            True if analysis should be performed
        """
        # Check if feature is enabled
        if not sentiment_config.enabled:
            return False
        
        # Always analyze first message or first reply
        if is_first_message:
            logger.info(f"😊 [SENTIMENT] Analyzing first message for conversation {conversation_id}")
            return True
        
        # Get current sentiment data to check if this is the first reply
        current_sentiment = await self.get_conversation_sentiment(conversation_id)
        
        # If no sentiment data exists, this might be the first reply
        if not current_sentiment:
            logger.info(f"😊 [SENTIMENT] No sentiment data found, analyzing for conversation {conversation_id}")
            return True
        
        # Check if we should analyze based on interval (every 3rd message)
        if message_count % sentiment_config.analysis_interval_messages == 0:
            logger.info(f"😊 [SENTIMENT] Analyzing every {sentiment_config.analysis_interval_messages}th message (count: {message_count}) for conversation {conversation_id}")
            return True
        
        logger.info(f"🚫 [SENTIMENT] Skipping analysis for message count {message_count} in conversation {conversation_id}")
        return False
    
    def _is_valid_message_for_analysis(self, message_text: str) -> bool:
        """
        Check if message is valid for sentiment analysis.
        
        Args:
            message_text: Message text to validate
            
        Returns:
            True if message is valid for analysis
        """
        if not message_text or not message_text.strip():
            return False
        
        text_length = len(message_text.strip())
        
        if text_length < sentiment_config.min_message_length:
            return False
        
        if text_length > sentiment_config.max_message_length:
            return False
        
        # Skip very short messages that are likely just acknowledgments
        if text_length < 10 and message_text.lower().strip() in [
            "ok", "okay", "yes", "no", "thanks", "thank you", "gracias", "si", "no"
        ]:
            return False
        
        return True
    
    async def _store_sentiment_data(self, sentiment_response: SentimentAnalysisResponse):
        """
        Store sentiment data in database.
        
        Args:
            sentiment_response: Sentiment analysis response
        """
        try:
            db = await self._get_db()
            
            # Get existing sentiment data
            existing_doc = await db.conversation_sentiments.find_one(
                {"conversation_id": sentiment_response.conversation_id}
            )
            
            if existing_doc:
                # Update existing sentiment data
                sentiment_data = ConversationSentimentData(**existing_doc["sentiment_data"])
                sentiment_data.current_sentiment = sentiment_response.sentiment_emoji
                sentiment_data.sentiment_history.append(sentiment_response)
                sentiment_data.last_analyzed_message_id = sentiment_response.message_id
                sentiment_data.message_count_at_last_analysis = await self._get_message_count(
                    sentiment_response.conversation_id
                )
                sentiment_data.updated_at = datetime.now(timezone.utc)
                
                # Keep only last 10 sentiment analyses
                if len(sentiment_data.sentiment_history) > 10:
                    sentiment_data.sentiment_history = sentiment_data.sentiment_history[-10:]
                
                # Update in database
                await db.conversation_sentiments.update_one(
                    {"conversation_id": sentiment_response.conversation_id},
                    {
                        "$set": {
                            "sentiment_data": sentiment_data.dict(),
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
                
                # Update cache
                cache_key = f"sentiment_{sentiment_response.conversation_id}"
                self._cache[cache_key] = sentiment_data
                
            else:
                # Create new sentiment data
                sentiment_data = ConversationSentimentData(
                    conversation_id=sentiment_response.conversation_id,
                    current_sentiment=sentiment_response.sentiment_emoji,
                    sentiment_history=[sentiment_response],
                    last_analyzed_message_id=sentiment_response.message_id,
                    message_count_at_last_analysis=await self._get_message_count(
                        sentiment_response.conversation_id
                    )
                )
                
                # Store in database
                stored_sentiment = StoredConversationSentiment(
                    conversation_id=sentiment_response.conversation_id,
                    sentiment_data=sentiment_data
                )
                
                await db.conversation_sentiments.insert_one(stored_sentiment.dict())
                
                # Update cache
                cache_key = f"sentiment_{sentiment_response.conversation_id}"
                self._cache[cache_key] = sentiment_data
            
            logger.info(f"✅ Stored sentiment data for conversation {sentiment_response.conversation_id}")
            
        except Exception as e:
            logger.error(f"❌ Error storing sentiment data: {str(e)}")
            raise
    
    async def _load_customer_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Load all customer messages for a conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of customer message dictionaries
        """
        try:
            # Use cursor message service to get all messages
            messages_result = await cursor_message_service.get_messages_cursor(
                conversation_id=conversation_id,
                limit=1000  # Get all messages
            )
            
            messages = messages_result.get("messages", [])
            
            # Filter only customer messages
            customer_messages = []
            for msg in messages:
                if msg.get("sender_role") == "customer" or msg.get("direction") == "inbound":
                    customer_messages.append(msg)
            
            # Sort by timestamp
            customer_messages.sort(key=lambda x: x.get("timestamp", x.get("created_at", "")))
            
            logger.info(f"Loaded {len(customer_messages)} customer messages for sentiment analysis")
            return customer_messages
            
        except Exception as e:
            logger.error(f"Error loading customer messages for conversation {conversation_id}: {str(e)}")
            return []
    
    async def _get_message_count(self, conversation_id: str) -> int:
        """
        Get message count for a conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Message count
        """
        try:
            conversation = await conversation_service.get_conversation(conversation_id)
            return conversation.get("message_count", 0) if conversation else 0
        except Exception as e:
            logger.warning(f"Could not get message count for conversation {conversation_id}: {str(e)}")
            return 0
    
    async def _notify_sentiment_update(self, sentiment_response: SentimentAnalysisResponse):
        """
        Send WebSocket notification for sentiment update.
        
        Args:
            sentiment_response: Sentiment analysis response
        """
        try:
            notification = SentimentWebSocketNotification(
                conversation_id=sentiment_response.conversation_id,
                sentiment_emoji=sentiment_response.sentiment_emoji,
                confidence=sentiment_response.confidence,
                message_id=sentiment_response.message_id
            )
            
            # Send notification via WebSocket service
            await websocket_service.notify_sentiment_update(
                conversation_id=sentiment_response.conversation_id,
                sentiment_emoji=sentiment_response.sentiment_emoji,
                confidence=sentiment_response.confidence,
                message_id=sentiment_response.message_id
            )
            
            logger.info(f"🔔 Sent sentiment update notification for conversation {sentiment_response.conversation_id}")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to send sentiment update notification: {str(e)}")
    
    async def process_incoming_message_sentiment(
        self,
        conversation_id: str,
        message_id: str,
        message_text: str,
        customer_phone: str,
        is_first_message: bool = False
    ):
        """
        Process sentiment analysis for an incoming message.
        This is called from the webhook to analyze customer messages.
        
        Args:
            conversation_id: Conversation ID
            message_id: Message ID
            message_text: Message text
            customer_phone: Customer phone number
            is_first_message: Whether this is the first message
        """
        try:
            logger.info(f"😊 [SENTIMENT] Starting process_incoming_message_sentiment for conversation {conversation_id}")
            
            # Get message count
            conversation = await conversation_service.get_conversation(conversation_id)
            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found for sentiment analysis")
                return
            
            message_count = conversation.get("message_count", 0)
            logger.info(f"😊 [SENTIMENT] Message count: {message_count}, is_first_message: {is_first_message}")
            
            # Create sentiment analysis request
            request = SentimentAnalysisRequest(
                conversation_id=conversation_id,
                message_id=message_id,
                message_text=message_text,
                customer_phone=customer_phone,
                message_count=message_count,
                is_first_message=is_first_message
            )
            
            logger.info(f"😊 [SENTIMENT] Created request, calling analyze_message_sentiment")
            
            # Analyze sentiment
            result = await self.analyze_message_sentiment(request)
            
            logger.info(f"😊 [SENTIMENT] analyze_message_sentiment completed, success: {result.success}")
            
            if result.success:
                logger.info(
                    f"✅ Sentiment analysis completed for message {message_id}: "
                    f"{result.response.sentiment_emoji} (confidence: {result.response.confidence:.2f})"
                )
            else:
                logger.warning(f"⚠️ Sentiment analysis failed for message {message_id}: {result.error}")
                
        except Exception as e:
            logger.error(f"❌ Error processing sentiment for message {message_id}: {str(e)}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
