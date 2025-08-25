"""
Schemas for sentiment analyzer service.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class SentimentType(str, Enum):
    """Sentiment types."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class SentimentEmoji(str, Enum):
    """Available sentiment emojis."""
    HAPPY = "😊"
    NEUTRAL = "😐"
    SAD = "😞"
    FRUSTRATED = "😤"
    ANGRY = "😡"
    THINKING = "🤔"
    CALM = "😌"
    ANXIOUS = "😰"
    LOVING = "😍"
    MELANCHOLY = "😔"


class SentimentAnalysisRequest(BaseModel):
    """Request for sentiment analysis."""
    conversation_id: str = Field(..., description="Conversation ID")
    message_id: str = Field(..., description="Message ID to analyze")
    message_text: str = Field(..., description="Message text to analyze")
    customer_phone: str = Field(..., description="Customer phone number")
    message_count: int = Field(..., description="Current message count in conversation")
    is_first_message: bool = Field(False, description="Whether this is the first message")
    language: Optional[str] = Field(None, description="Detected language of the message")


class SentimentAnalysisResponse(BaseModel):
    """Response from sentiment analysis."""
    conversation_id: str = Field(..., description="Conversation ID")
    message_id: str = Field(..., description="Message ID analyzed")
    sentiment_type: SentimentType = Field(..., description="Detected sentiment type")
    sentiment_emoji: SentimentEmoji = Field(..., description="Sentiment emoji")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    reasoning: Optional[str] = Field(None, description="Reasoning for sentiment choice")
    language: str = Field(..., description="Detected language")
    analyzed_at: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class SentimentAnalysisResult(BaseModel):
    """Result of sentiment analysis process."""
    success: bool = Field(..., description="Whether analysis was successful")
    response: Optional[SentimentAnalysisResponse] = Field(None, description="Analysis response")
    error: Optional[str] = Field(None, description="Error message if failed")
    processing_time: float = Field(..., description="Total processing time in seconds")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")


class ConversationSentimentData(BaseModel):
    """Sentiment data for a conversation."""
    conversation_id: str = Field(..., description="Conversation ID")
    current_sentiment: Optional[SentimentEmoji] = Field(None, description="Current sentiment emoji")
    sentiment_history: List[SentimentAnalysisResponse] = Field(
        default_factory=list, 
        description="History of sentiment analyses"
    )
    last_analyzed_message_id: Optional[str] = Field(None, description="Last analyzed message ID")
    message_count_at_last_analysis: int = Field(0, description="Message count at last analysis")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")


class StoredConversationSentiment(BaseModel):
    """Stored conversation sentiment in MongoDB."""
    conversation_id: str = Field(..., description="Conversation ID")
    sentiment_data: ConversationSentimentData = Field(..., description="Sentiment data")
    created_at: datetime = Field(default_factory=datetime.now, description="When sentiment was first created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When sentiment was last updated")
    version: int = Field(1, description="Sentiment data version number")


class SentimentAnalysisConfig(BaseModel):
    """Configuration for sentiment analysis."""
    enabled: bool = Field(True, description="Whether sentiment analysis is enabled")
    analysis_interval: int = Field(3, description="Analyze every N messages")
    min_message_length: int = Field(5, description="Minimum message length to analyze")
    max_message_length: int = Field(1000, description="Maximum message length to analyze")
    confidence_threshold: float = Field(0.6, description="Minimum confidence threshold")
    language: str = Field("auto", description="Language for analysis (auto for detection)")


class SentimentWebSocketNotification(BaseModel):
    """WebSocket notification for sentiment updates."""
    type: str = Field("sentiment_update", description="Notification type")
    conversation_id: str = Field(..., description="Conversation ID")
    sentiment_emoji: SentimentEmoji = Field(..., description="New sentiment emoji")
    confidence: float = Field(..., description="Confidence score")
    message_id: str = Field(..., description="Message ID that triggered the update")
    timestamp: datetime = Field(default_factory=datetime.now, description="Update timestamp")
