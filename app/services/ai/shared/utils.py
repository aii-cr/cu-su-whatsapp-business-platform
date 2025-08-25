"""
Shared utilities for AI services.
Simple replacements for common functions.
"""

import re
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from langchain.tools import BaseTool
from pydantic import BaseModel, Field


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
    
    # Check if it's a valid MongoDB ObjectId format
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


class ToolResult(BaseModel):
    """Standard result structure for tool operations."""
    success: bool = Field(..., description="Whether the operation was successful")
    data: Optional[Dict[str, Any]] = Field(None, description="Result data")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


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
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._arun(*args, **kwargs))
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(self._arun(*args, **kwargs))
    
    def _log_usage(self, **kwargs):
        """Log tool usage for monitoring."""
        self._last_used = datetime.now()
        # Simple logging placeholder
