# NEW CODE
"""
Definición del estado del agente para LangGraph.
"""

from __future__ import annotations
from typing import List, TypedDict, Optional, Any, Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """Estado: mensajes, id, intentos y el idioma objetivo."""
    messages: Annotated[List[AnyMessage], add_messages]
    conversation_id: str
    attempts: int
    target_language: str
    summary: Optional[str]
