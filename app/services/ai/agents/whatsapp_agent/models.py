# NEW CODE
"""
Modelos de chat y embeddings - ahora importa desde shared para evitar imports circulares.
"""

from __future__ import annotations
from typing import Optional
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Import from shared location to avoid circular imports
from app.services.ai.shared.models import get_chat_model, get_embedding_model

# Re-export for backward compatibility
__all__ = ["get_chat_model", "get_embedding_model"]
