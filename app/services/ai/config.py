"""
AI service configuration.
Reads from core/config.Settings and provides AI-specific configuration.
"""

from typing import Optional
from pydantic import BaseModel
from app.core.config import settings


class AIConfig(BaseModel):
    """AI service configuration loaded from core settings."""
    
    # OpenAI Configuration
    openai_api_key: str = settings.OPENAI_API_KEY
    openai_model: str = settings.OPENAI_MODEL
    openai_embedding_model: str = settings.OPENAI_EMBEDDING_MODEL
    openai_embedding_dimension: int = settings.OPENAI_EMBEDDING_DIMENSION
    
    # Qdrant Configuration
    qdrant_url: str = settings.QDRANT_URL
    qdrant_api_key: str = settings.QDRANT_API_KEY
    qdrant_collection_name: str = settings.QDRANT_COLLECTION_NAME
    
    # LangChain Configuration
    langchain_tracing_v2: bool = settings.LANGCHAIN_TRACING_V2
    langchain_project: str = settings.LANGCHAIN_PROJECT
    langchain_api_key: str = settings.LANGCHAIN_API_KEY
    
    # Agent Configuration
    max_retries: int = 3
    timeout_seconds: int = 30
    confidence_threshold: float = 0.5  # Balanced threshold for production
    rag_retrieval_k: int = 6
    max_context_tokens: int = 4000
    
    # WhatsApp Configuration
    max_response_length: int = 700
    default_language: str = "es"  # Spanish for Costa Rica
    supported_languages: list[str] = ["es", "en"]
    
    # Safety Configuration
    enable_content_filtering: bool = True
    max_processing_time_seconds: int = 10
    
    class Config:
        frozen = True


# Global AI config instance
ai_config = AIConfig()
