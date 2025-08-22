"""
Tools for the Writer Agent.
"""

from .conversation_tool import create_conversation_context_tool
from .rag_tool import create_rag_tool

def get_writer_tool_belt():
    """Get all tools for the Writer Agent."""
    return [
        create_conversation_context_tool(),
        create_rag_tool()
    ]

__all__ = [
    "create_conversation_context_tool", 
    "create_rag_tool",
    "get_writer_tool_belt"
]
