"""
Base tools and utilities for AI agents.
Provides common tool patterns and base classes for agent tools.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field

from app.core.logger import logger


class BaseAgentTool(BaseTool, ABC):
    """
    Base class for all agent tools with common functionality.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._last_used: Optional[datetime] = None
    
    @abstractmethod
    async def _arun(self, *args, **kwargs) -> str:
        """Async implementation of the tool."""
        pass
    
    def _run(self, *args, **kwargs) -> str:
        """Sync implementation - delegates to async."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._arun(*args, **kwargs))
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(self._arun(*args, **kwargs))
    
    def _log_usage(self, **kwargs):
        """Log tool usage for monitoring."""
        self._last_used = datetime.now()
        logger.info(f"Tool {self.name} used with args: {kwargs}")


class ToolResult(BaseModel):
    """Standard result structure for tool operations."""
    success: bool = Field(..., description="Whether the operation was successful")
    data: Optional[Dict[str, Any]] = Field(None, description="Result data")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ConversationContext(BaseModel):
    """Context information for conversation processing."""
    conversation_id: str = Field(..., description="Conversation identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_data: Dict[str, Any] = Field(default_factory=dict, description="Session data")
    message_history: List[Dict[str, Any]] = Field(default_factory=list, description="Message history")


def validate_conversation_id(conversation_id: str) -> bool:
    """
    Validate conversation ID format.
    
    Args:
        conversation_id: Conversation ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not conversation_id or not isinstance(conversation_id, str):
        return False
    
    # Add your validation logic here
    # For example, check if it's a valid MongoDB ObjectId format
    import re
    return bool(re.match(r'^[a-fA-F0-9]{24}$', conversation_id))


def sanitize_text(text: str, max_length: int = 1000) -> str:
    """
    Sanitize text for safe processing.
    
    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    text = text.replace('\x00', '')  # Null bytes
    text = text.replace('\r', '\n')  # Normalize line endings
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text.strip()


def format_timestamp(timestamp: datetime) -> str:
    """
    Format timestamp for consistent display.
    
    Args:
        timestamp: Datetime to format
        
    Returns:
        Formatted timestamp string
    """
    return timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from text for summarization.
    
    Args:
        text: Text to extract keywords from
        max_keywords: Maximum number of keywords to extract
        
    Returns:
        List of keywords
    """
    if not text:
        return []
    
    # Simple keyword extraction - in production, use more sophisticated NLP
    import re
    from collections import Counter
    
    # Remove common words and punctuation
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
    
    # Extract words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Filter out stop words and count
    keywords = [word for word in words if word not in stop_words]
    word_counts = Counter(keywords)
    
    # Return most common keywords
    return [word for word, count in word_counts.most_common(max_keywords)]

