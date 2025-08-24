# NEW CODE
"""
RAG retriever tool - alias to the existing retrieve_information tool.
"""

from __future__ import annotations
from app.services.ai.shared.tools.rag.retriever import retrieve_information

# Export the existing RAG tool
__all__ = ["retrieve_information"]
