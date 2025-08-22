"""
AI services module.
Provides access to all AI-related services and agents.
"""

from .config import ai_config
from .shared.memory_service import memory_service
from .agents.whatsapp.agent_service import agent_service

# Import RAG components
from .rag.ingest import ingest_documents, check_collection_health
from .rag.retriever import build_retriever as get_retriever
from .rag.schemas import IngestionResult

__all__ = [
    "ai_config",
    "memory_service", 
    "agent_service",
    "ingest_documents",
    "check_collection_health",
    "get_retriever",
    "IngestionResult"
]
