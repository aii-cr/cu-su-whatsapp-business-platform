# NEW CODE
"""
Definición del estado del agente para LangGraph.
"""

from __future__ import annotations
from typing import List, TypedDict, Optional, Any
from langchain_core.messages import AnyMessage


class AgentState(TypedDict, total=False):
    """Estado: mensajes, id, intentos y el idioma objetivo."""
    messages: List[AnyMessage]
    conversation_id: str
    attempts: int
    target_language: str
    summary: Optional[str]
