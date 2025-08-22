"""
Schemas for conversation summarizer service.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ConversationSummaryRequest(BaseModel):
    """Request to summarize a conversation."""
    conversation_id: str = Field(..., description="Conversation ID to summarize")
    include_metadata: bool = Field(True, description="Whether to include metadata in summary")
    summary_type: str = Field("general", description="Type of summary to generate")
    user_id: Optional[str] = Field(None, description="User ID who requested the summary")


class ConversationSummaryResponse(BaseModel):
    """Response containing conversation summary."""
    conversation_id: str = Field(..., description="Conversation ID")
    summary: str = Field(..., description="Generated summary in markdown format")
    key_points: List[str] = Field(default_factory=list, description="Key points from conversation")
    sentiment: Optional[str] = Field(None, description="Overall sentiment of conversation")
    sentiment_emoji: Optional[str] = Field(None, description="Emoji representing customer sentiment")
    topics: List[str] = Field(default_factory=list, description="Main topics discussed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    generated_at: datetime = Field(default_factory=datetime.now, description="When summary was generated")
    generated_by: Optional[str] = Field(None, description="User ID who generated the summary")
    message_count: int = Field(..., description="Number of messages processed")
    ai_message_count: int = Field(0, description="Number of AI assistant messages")
    human_agents: List[Dict[str, str]] = Field(default_factory=list, description="Human agents in conversation")
    customer: Optional[Dict[str, str]] = Field(None, description="Customer information")
    duration_minutes: Optional[float] = Field(None, description="Duration of conversation in minutes")


class MessageData(BaseModel):
    """Message data for summarization."""
    message_id: str = Field(..., description="Message ID")
    content: str = Field(..., description="Message content")
    role: str = Field(..., description="Message role (user/assistant)")
    sender_name: Optional[str] = Field(None, description="Sender name")
    sender_email: Optional[str] = Field(None, description="Sender email")
    timestamp: datetime = Field(..., description="Message timestamp")
    message_type: str = Field("text", description="Type of message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Message metadata")


class ConversationData(BaseModel):
    """Conversation data for summarization."""
    conversation_id: str = Field(..., description="Conversation ID")
    messages: List[MessageData] = Field(..., description="List of messages")
    participants: List[str] = Field(default_factory=list, description="Participant IDs")
    human_agents: List[Dict[str, str]] = Field(default_factory=list, description="Human agents in conversation")
    customer: Optional[Dict[str, str]] = Field(None, description="Customer information")
    start_time: Optional[datetime] = Field(None, description="Conversation start time")
    end_time: Optional[datetime] = Field(None, description="Conversation end time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Conversation metadata")


class SummarizationConfig(BaseModel):
    """Configuration for summarization."""
    max_summary_length: int = Field(500, description="Maximum summary length in words")
    include_key_points: bool = Field(True, description="Whether to include key points")
    include_sentiment: bool = Field(True, description="Whether to include sentiment analysis")
    include_topics: bool = Field(True, description="Whether to include topic extraction")
    language: str = Field("auto", description="Language for summarization")
    style: str = Field("professional", description="Summary style (professional, casual, technical)")


class SummarizationResult(BaseModel):
    """Result of summarization process."""
    success: bool = Field(..., description="Whether summarization was successful")
    summary: Optional[ConversationSummaryResponse] = Field(None, description="Generated summary")
    error: Optional[str] = Field(None, description="Error message if failed")
    processing_time: float = Field(..., description="Time taken to process in seconds")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")


class StoredConversationSummary(BaseModel):
    """Stored conversation summary in MongoDB."""
    conversation_id: str = Field(..., description="Conversation ID")
    summary_data: ConversationSummaryResponse = Field(..., description="Summary data")
    created_at: datetime = Field(default_factory=datetime.now, description="When summary was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When summary was last updated")
    created_by: Optional[str] = Field(None, description="User ID who created the summary")
    version: int = Field(1, description="Summary version number")
