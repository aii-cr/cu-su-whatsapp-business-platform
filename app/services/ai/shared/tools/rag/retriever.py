# OPTIMIZED CODE
"""
High-performance RAG retriever with caching, connection pooling, and async support.
Optimized for speed while maintaining quality through intelligent query strategies.
"""

from __future__ import annotations
import asyncio
import time
from typing import Annotated, List, Optional, Dict, Any

from langchain_core.tools import tool
from langchain_core.documents import Document

from app.services.ai.shared.connection_pool import connection_pool
from app.services.ai.shared.retrieval_cache import retrieval_cache
from app.services.ai.shared.performance_monitor import performance_monitor, RetrievalMetrics
from app.services.ai.config import ai_config
from app.core.logger import logger


def _determine_retrieval_strategy(query: str) -> Dict[str, Any]:
    """Determine optimal retrieval strategy based on query characteristics."""
    query_lower = query.lower().strip()
    query_len = len(query.split())
    
    # Fast strategy for simple/common queries
    use_fast_mode = (
        query_len <= 3 or  # Very short queries
        any(term in query_lower for term in [
            "hola", "hello", "hi", "precio", "price", "plan", "servicio", "service"
        ])
    )
    
    return {
        "use_multiquery": not use_fast_mode,  # Skip MultiQuery for simple queries
        "use_rerank": True,  # Always use rerank for quality
        "cache_ttl": 600 if use_fast_mode else 300,  # Longer cache for simple queries
        "strategy": "fast" if use_fast_mode else "comprehensive"
    }


async def _fast_retrieve(query: str, strategy: Dict[str, Any]) -> List[Document]:
    """Fast retrieval path without MultiQuery for better performance."""
    try:
        # Try cache first
        cached_results = retrieval_cache.get_cached_results(query, strategy)
        if cached_results:
            return cached_results
        
        logger.info(f"🚀 [RAG] Fast retrieval for query: '{query[:50]}...'")
        
        # Use pooled retriever with compression
        retriever = connection_pool.get_compression_retriever(use_multiquery=False)
        
        # Execute retrieval
        docs = await asyncio.to_thread(retriever.get_relevant_documents, query)
        
        # Cache results
        retrieval_cache.cache_results(query, docs, strategy, strategy["cache_ttl"])
        
        logger.info(f"✅ [RAG] Fast retrieval completed: {len(docs)} documents")
        return docs
        
    except Exception as e:
        logger.error(f"❌ [RAG] Fast retrieval failed: {str(e)}")
        raise


async def _comprehensive_retrieve(query: str, strategy: Dict[str, Any]) -> List[Document]:
    """Comprehensive retrieval with MultiQuery for complex queries."""
    try:
        # Try cache first
        cached_results = retrieval_cache.get_cached_results(query, strategy)
        if cached_results:
            return cached_results
        
        logger.info(f"🎯 [RAG] Comprehensive retrieval for query: '{query[:50]}...'")
        
        # Use pooled retriever with MultiQuery
        retriever = connection_pool.get_compression_retriever(use_multiquery=True)
        
        # Execute retrieval with timeout
        docs = await asyncio.wait_for(
            asyncio.to_thread(retriever.get_relevant_documents, query),
            timeout=15.0  # 15 second timeout for comprehensive retrieval
        )
        
        # Cache results
        retrieval_cache.cache_results(query, docs, strategy, strategy["cache_ttl"])
        
        logger.info(f"✅ [RAG] Comprehensive retrieval completed: {len(docs)} documents")
        return docs
        
    except asyncio.TimeoutError:
        logger.warning("⏰ [RAG] Comprehensive retrieval timed out, falling back to fast mode")
        # Fallback to fast retrieval on timeout
        strategy["use_multiquery"] = False
        return await _fast_retrieve(query, strategy)
    except Exception as e:
        logger.error(f"❌ [RAG] Comprehensive retrieval failed: {str(e)}")
        raise


def _format_docs(docs: List[Document]) -> str:
    """Formatea contexto en texto compacto con etiquetas de origen."""
    try:
        logger.info(f"📄 [RAG] Formatting {len(docs)} retrieved documents")
        
        parts = []
        for i, d in enumerate(docs):
            tag = d.metadata.get("slug") or d.metadata.get("title") or d.metadata.get("type", "doc")
            parts.append(f"[{tag}] {d.page_content}")
            logger.debug(f"📄 [RAG] Doc {i+1}: [{tag}] {d.page_content[:100]}...")
            
        formatted_context = "\n\n---\n\n".join(parts)
        logger.info(f"✅ [RAG] Documents formatted successfully, total length: {len(formatted_context)} chars")
        
        return formatted_context
        
    except Exception as e:
        logger.error(f"❌ [RAG] Failed to format documents: {str(e)}")
        return ""


@tool("adn_retrieve", return_direct=False)
async def retrieve_information(query: Annotated[str, "consulta del cliente"]) -> str:
    """
    High-performance RAG retrieval with intelligent strategy selection.
    Uses caching and connection pooling for optimal speed while maintaining quality.
    """
    start_time = time.time()
    strategy = None
    cache_hit = False
    docs = []
    error = None
    
    try:
        logger.info(f"🔍 [RAG] Starting optimized retrieval for query: '{query[:100]}...'")
        
        # Step 1: Determine optimal retrieval strategy
        strategy = _determine_retrieval_strategy(query)
        logger.info(f"📋 [RAG] Using {strategy['strategy']} strategy (multiquery: {strategy['use_multiquery']})")
        
        # Step 2: Check cache first
        cached_results = retrieval_cache.get_cached_results(query, strategy)
        if cached_results:
            docs = cached_results
            cache_hit = True
            logger.info(f"🎯 [RAG] Cache hit! Retrieved {len(docs)} documents from cache")
        else:
            # Step 3: Execute retrieval based on strategy
            if strategy["use_multiquery"]:
                docs = await _comprehensive_retrieve(query, strategy)
            else:
                docs = await _fast_retrieve(query, strategy)
        
        logger.info(f"📊 [RAG] Retrieved {len(docs)} documents for query")
        
        if not docs:
            logger.warning("⚠️ [RAG] No documents found for query")
            return "NO_CONTEXT_AVAILABLE: La base de conocimiento está vacía o no contiene información relevante para esta consulta."
            
        # Step 4: Format and return
        formatted_context = _format_docs(docs)
        
        logger.info(f"✅ [RAG] Optimized retrieval completed successfully")
        return formatted_context
        
    except Exception as e:
        error = str(e)
        logger.error(f"❌ [RAG] Optimized retrieval failed: {error}")
        
        # If it's a collection not found error, return no context signal
        if "doesn't exist" in error or "not found" in error.lower():
            logger.info("🏗️ [RAG] Collection doesn't exist yet, will be created on first use")
            return "NO_CONTEXT_AVAILABLE: La base de conocimiento aún no ha sido inicializada. Será creada automáticamente."
        
        # For other errors, return error signal
        return "ERROR_ACCESSING_KNOWLEDGE: No se pudo acceder a la información en este momento."
        
    finally:
        # Record performance metrics
        end_time = time.time()
        total_time_ms = (end_time - start_time) * 1000
        
        metrics = RetrievalMetrics(
            query=query,
            strategy=strategy["strategy"] if strategy else "unknown",
            total_time_ms=total_time_ms,
            cache_hit=cache_hit,
            documents_found=len(docs),
            error=error
        )
        
        performance_monitor.record_retrieval(metrics)


# Backward compatibility - sync wrapper
def retrieve_information_sync(query: str) -> str:
    """Synchronous wrapper for backward compatibility."""
    try:
        return asyncio.run(retrieve_information(query))
    except Exception as e:
        logger.error(f"❌ [RAG] Sync wrapper failed: {str(e)}")
        return "ERROR_ACCESSING_KNOWLEDGE: No se pudo acceder a la información en este momento."
