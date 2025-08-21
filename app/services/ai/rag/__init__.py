"""
RAG (Retrieval-Augmented Generation) components for AI chatbot.
Includes ingestion, retrieval, and document processing.
"""

from .retriever import build_retriever, RetrieverConfig
from .ingest import ingest_documents, check_collection_health
from .schemas import DocumentChunk, RetrievalResult

__all__ = [
    "build_retriever", 
    "RetrieverConfig", 
    "ingest_documents", 
    "check_collection_health",
    "DocumentChunk", 
    "RetrievalResult"
]
