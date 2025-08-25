"""
Shared AI models for all services and agents.
Centralized model creation to avoid circular imports.
"""

from __future__ import annotations
from typing import Optional
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.services.ai.config import ai_config
from app.core.logger import logger


def get_chat_model(model_name: Optional[str] = None) -> ChatOpenAI:
    """Devuelve modelo de chat configurado con timeouts y reintentos seguros."""
    try:
        model = model_name or ai_config.openai_model
        logger.info(f"🤖 [MODELS] Creating chat model: {model}")
        
        chat_model = ChatOpenAI(
            model=model,
            api_key=ai_config.openai_api_key,
            temperature=0.2,
            timeout=ai_config.timeout_seconds,
            max_retries=ai_config.max_retries,
        )
        
        logger.info(f"✅ [MODELS] Chat model created successfully: {model}")
        return chat_model
        
    except Exception as e:
        logger.error(f"❌ [MODELS] Failed to create chat model: {str(e)}")
        raise


def get_embedding_model() -> OpenAIEmbeddings:
    """Devuelve el modelo de embeddings denso conforme a configuración."""
    try:
        logger.info(f"🔤 [MODELS] Creating embedding model: {ai_config.openai_embedding_model}")
        
        embedding_model = OpenAIEmbeddings(
            model=ai_config.openai_embedding_model,
            api_key=ai_config.openai_api_key
        )
        
        logger.info(f"✅ [MODELS] Embedding model created successfully: {ai_config.openai_embedding_model}")
        return embedding_model
        
    except Exception as e:
        logger.error(f"❌ [MODELS] Failed to create embedding model: {str(e)}")
        raise
