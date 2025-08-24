"""
AI service configuration.
Reads from core/config.Settings and provides AI-specific configuration.
"""

from typing import Optional
from pydantic import BaseModel
from app.core.config import settings


# CHANGED / EXTENDED CODE
class AIConfig(BaseModel):
    # OpenAI...
    openai_api_key: str = settings.OPENAI_API_KEY
    openai_model: str = settings.OPENAI_MODEL
    openai_embedding_model: str = settings.OPENAI_EMBEDDING_MODEL
    openai_embedding_dimension: int = settings.OPENAI_EMBEDDING_DIMENSION

    # Qdrant...
    qdrant_url: str = settings.QDRANT_URL
    qdrant_api_key: str = settings.QDRANT_API_KEY
    qdrant_collection_name: str = settings.QDRANT_COLLECTION_NAME

    # LangSmith / LangChain
    langchain_tracing_v2: bool = settings.LANGCHAIN_TRACING_V2
    langchain_project: str = settings.LANGCHAIN_PROJECT
    langchain_api_key: str = settings.LANGCHAIN_API_KEY

    # Cohere (NEW)
    cohere_api_key: str = settings.COHERE_API_KEY

    # Agent
    max_retries: int = 3
    timeout_seconds: int = 30
    confidence_threshold: float = 0.5
    rag_retrieval_k: int = 12
    max_context_tokens: int = 4000

    # WhatsApp
    max_response_length: int = 1500
    default_language: str = "es"
    supported_languages: list[str] = ["es", "en"]

    # Safety
    enable_content_filtering: bool = True
    max_processing_time_seconds: int = 10

    class Config:
        frozen = True


# Global AI config instance
ai_config = AIConfig()
