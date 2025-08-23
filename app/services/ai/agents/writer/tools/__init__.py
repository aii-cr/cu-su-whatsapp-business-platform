"""
Tools for the Writer Agent.
"""

from .conversation_tool import create_conversation_context_tool
from app.services.ai.shared.rag_tool import create_shared_rag_tool

def get_writer_tool_belt():
    """Get all tools for the Writer Agent."""
    return [
        create_conversation_context_tool(),
        create_shared_rag_tool()
    ]

__all__ = [
    "create_conversation_context_tool", 
    "create_shared_rag_tool",
    "get_writer_tool_belt"
]
