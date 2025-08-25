"""
Connection pooling and singleton management for RAG components.
Prevents recreation of expensive objects on every request.
"""

from typing import Optional, Dict, Any
from functools import lru_cache
import threading
import time

from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore, RetrievalMode, FastEmbedSparse
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_cohere.rerank import CohereRerank
from langchain_core.documents import Document

from app.services.ai.shared.models import get_embedding_model, get_chat_model
from app.services.ai.config import ai_config
from app.core.logger import logger


class ConnectionPool:
    """Singleton connection pool for RAG components."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized') or not self._initialized:
            self._qdrant_client: Optional[QdrantClient] = None
            self._vector_store: Optional[QdrantVectorStore] = None
            self._multiquery_retriever: Optional[MultiQueryRetriever] = None
            self._compression_retriever: Optional[ContextualCompressionRetriever] = None
            self._cohere_rerank: Optional[CohereRerank] = None
            self._last_health_check = 0
            self._health_check_interval = 60  # 1 minute
            self._connection_errors = 0
            self._max_connection_errors = 3
            self._initialized = True
            logger.info("🏊 [POOL] Connection pool initialized")
    
    def _is_healthy(self) -> bool:
        """Check if connections are healthy."""
        current_time = time.time()
        
        # Skip frequent health checks
        if current_time - self._last_health_check < self._health_check_interval:
            return self._connection_errors < self._max_connection_errors
        
        try:
            if self._qdrant_client:
                # Simple ping to check Qdrant health
                collections = self._qdrant_client.get_collections()
                self._connection_errors = 0  # Reset on success
                self._last_health_check = current_time
                return True
        except Exception as e:
            self._connection_errors += 1
            logger.warning(f"⚠️ [POOL] Health check failed ({self._connection_errors}/{self._max_connection_errors}): {str(e)}")
        
        return self._connection_errors < self._max_connection_errors
    
    def _reset_connections(self):
        """Reset all connections."""
        logger.info("🔄 [POOL] Resetting connections due to health check failure")
        self._qdrant_client = None
        self._vector_store = None
        self._multiquery_retriever = None
        self._compression_retriever = None
        self._cohere_rerank = None
        self._connection_errors = 0
    
    def get_qdrant_client(self) -> QdrantClient:
        """Get or create Qdrant client."""
        if not self._is_healthy():
            self._reset_connections()
        
        if self._qdrant_client is None:
            try:
                logger.info("🔗 [POOL] Creating new Qdrant client")
                self._qdrant_client = QdrantClient(
                    url=ai_config.qdrant_url,
                    api_key=ai_config.qdrant_api_key,
                    prefer_grpc=True,
                    timeout=ai_config.timeout_seconds,
                )
                logger.info("✅ [POOL] Qdrant client created successfully")
            except Exception as e:
                logger.error(f"❌ [POOL] Failed to create Qdrant client: {str(e)}")
                raise
        
        return self._qdrant_client
    
    def get_vector_store(self) -> QdrantVectorStore:
        """Get or create vector store."""
        if not self._is_healthy():
            self._reset_connections()
        
        if self._vector_store is None:
            try:
                logger.info("🏪 [POOL] Creating new vector store")
                
                # Get embeddings (these are lightweight to recreate)
                embeddings = get_embedding_model()
                sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")
                
                self._vector_store = QdrantVectorStore.from_existing_collection(
                    embedding=embeddings,
                    sparse_embedding=sparse_embeddings,
                    collection_name=ai_config.qdrant_collection_name,
                    url=ai_config.qdrant_url,
                    api_key=ai_config.qdrant_api_key,
                    prefer_grpc=True,
                    retrieval_mode=RetrievalMode.HYBRID,
                    vector_name="dense",
                    sparse_vector_name="sparse",
                )
                logger.info("✅ [POOL] Vector store created successfully")
            except Exception as e:
                logger.error(f"❌ [POOL] Failed to create vector store: {str(e)}")
                raise
        
        return self._vector_store
    
    def get_cohere_rerank(self) -> CohereRerank:
        """Get or create Cohere rerank compressor."""
        if self._cohere_rerank is None:
            try:
                logger.info("🎯 [POOL] Creating new Cohere rerank compressor")
                self._cohere_rerank = CohereRerank(
                    cohere_api_key=ai_config.cohere_api_key,
                    model="rerank-multilingual-v3.0",
                    top_n=min(6, ai_config.rag_retrieval_k),  # Reduced from 8 for speed
                )
                logger.info("✅ [POOL] Cohere rerank compressor created successfully")
            except Exception as e:
                logger.error(f"❌ [POOL] Failed to create Cohere rerank: {str(e)}")
                raise
        
        return self._cohere_rerank
    
    def get_base_retriever(self):
        """Get optimized base retriever without MultiQuery for faster performance."""
        vector_store = self.get_vector_store()
        return vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": ai_config.rag_retrieval_k,
                "fetch_k": max(16, ai_config.rag_retrieval_k * 2),  # Slightly increased for better recall
                "lambda_mult": 0.7  # Balance between relevance and diversity
            },
        )
    
    def get_multiquery_retriever(self):
        """Get MultiQuery retriever (expensive, use sparingly)."""
        if self._multiquery_retriever is None:
            try:
                logger.info("🔍 [POOL] Creating new MultiQuery retriever")
                base_retriever = self.get_base_retriever()
                llm = get_chat_model()
                
                self._multiquery_retriever = MultiQueryRetriever.from_llm(
                    retriever=base_retriever, 
                    llm=llm, 
                    include_original=True
                )
                logger.info("✅ [POOL] MultiQuery retriever created successfully")
            except Exception as e:
                logger.error(f"❌ [POOL] Failed to create MultiQuery retriever: {str(e)}")
                raise
        
        return self._multiquery_retriever
    
    def get_compression_retriever(self, use_multiquery: bool = False):
        """Get compression retriever with optional MultiQuery."""
        try:
            logger.info(f"🎯 [POOL] Creating compression retriever (multiquery: {use_multiquery})")
            
            # Choose base retriever based on performance needs
            if use_multiquery:
                base_retriever = self.get_multiquery_retriever()
            else:
                base_retriever = self.get_base_retriever()
            
            compressor = self.get_cohere_rerank()
            
            compression_retriever = ContextualCompressionRetriever(
                base_compressor=compressor,
                base_retriever=base_retriever
            )
            
            logger.info("✅ [POOL] Compression retriever created successfully")
            return compression_retriever
            
        except Exception as e:
            logger.error(f"❌ [POOL] Failed to create compression retriever: {str(e)}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        return {
            "qdrant_client_active": self._qdrant_client is not None,
            "vector_store_active": self._vector_store is not None,
            "multiquery_retriever_active": self._multiquery_retriever is not None,
            "compression_retriever_active": self._compression_retriever is not None,
            "cohere_rerank_active": self._cohere_rerank is not None,
            "connection_errors": self._connection_errors,
            "last_health_check": self._last_health_check,
            "healthy": self._is_healthy()
        }
    
    def reset_pool(self):
        """Force reset the entire connection pool."""
        logger.info("🔄 [POOL] Force resetting connection pool")
        self._reset_connections()


# Global connection pool instance
connection_pool = ConnectionPool()
