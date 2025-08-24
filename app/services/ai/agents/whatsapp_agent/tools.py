# NEW CODE
"""
Toolbelt del agente (por ahora solo RAG).
Usa la versión sincrónica para compatibilidad con LangGraph.
"""

from __future__ import annotations
from typing import List, Any
from app.services.ai.shared.tools.rag.retriever import retrieve_information


def get_tool_belt() -> List[Any]:
    """Lista de herramientas disponibles - MISMAS que el Writer agent."""
    return [retrieve_information]  # Usar EXACTAMENTE la misma tool que el Writer agent
