"""
Writer Agent for generating contextual responses with helpfulness validation.

This agent helps human agents craft better responses by:
1. Analyzing conversation context
2. Using RAG to get relevant information
3. Generating well-crafted responses
4. Validating helpfulness in an iterative loop
"""

from .agent_service import WriterAgent

__all__ = ["WriterAgent"]
