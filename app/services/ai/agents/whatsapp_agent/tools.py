# NEW CODE
"""
Toolbelt del agente (por ahora solo RAG).
"""

from __future__ import annotations
from typing import List, Any
from .rag.retriever import retrieve_information


def get_tool_belt() -> List[Any]:
    """Lista de herramientas disponibles."""
    return [retrieve_information]
