"""
Tools for the Writer Agent.
"""

from .conversation_tool import create_conversation_context_tool
from app.services.ai.shared.tools.rag.retriever import retrieve_information

def get_writer_tool_belt():
    """Get all tools for the Writer Agent."""
    return [
        create_conversation_context_tool(),
        retrieve_information  # Using the new RAG tool directly
    ]

def create_shared_rag_tool():
    """Backward compatibility function - returns the new retrieve_information tool."""
    return retrieve_information

__all__ = [
    "create_conversation_context_tool", 
    "create_shared_rag_tool",
    "get_writer_tool_belt"
]
