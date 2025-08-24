"""
Sentiment analyzer configuration.
Contains settings for sentiment analysis feature.
"""

from typing import List
from pydantic import BaseModel, Field
from app.services.ai.config import ai_config


class SentimentAnalyzerConfig(BaseModel):
    """Configuration for sentiment analysis."""
    
    # Analysis Settings
    analysis_interval_messages: int = Field(1, description="Analyze sentiment every N customer messages")
    max_message_length: int = Field(1000, description="Maximum message length to analyze")
    min_message_length: int = Field(1, description="Minimum message length to analyze")
    
    # Sentiment Emojis
    sentiment_emojis: List[str] = Field(
        default=["😊", "😐", "😞", "😤", "😡", "🤔", "😌", "😰", "😍", "😔"],
        description="Available sentiment emojis"
    )
    
    # Model Configuration
    model_name: str = Field(default=ai_config.openai_model, description="Model for sentiment analysis")
    temperature: float = Field(0.1, description="Temperature for sentiment analysis")
    max_tokens: int = Field(10, description="Maximum tokens for sentiment response (just emoji)")
    
    # Processing Settings
    enable_async_processing: bool = Field(True, description="Enable async background processing")
    cache_duration_minutes: int = Field(30, description="Cache sentiment results for N minutes")
    max_retries: int = Field(2, description="Maximum retries for sentiment analysis")
    timeout_seconds: int = Field(10, description="Timeout for sentiment analysis")
    
    # Feature Flags
    enabled: bool = Field(True, description="Enable sentiment analysis feature")
    analyze_first_message: bool = Field(True, description="Analyze sentiment on first message")
    analyze_replies: bool = Field(True, description="Analyze sentiment on agent replies")
    
    # Performance Settings
    batch_size: int = Field(5, description="Batch size for processing multiple messages")
    rate_limit_per_minute: int = Field(20, description="Rate limit for sentiment analysis calls")
    
    class Config:
        frozen = True


# Global sentiment analyzer config instance
sentiment_config = SentimentAnalyzerConfig()
