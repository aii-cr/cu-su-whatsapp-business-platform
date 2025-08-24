# NEW CODE
"""
Retriever híbrido: MMR + MultiQuery + Cohere Rerank (multilingual).
Devuelve solo contexto (string) para que el LLM principal genere la respuesta.
"""

from __future__ import annotations
from typing import Annotated, List, Optional

from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, SparseVectorParams
from langchain_qdrant import QdrantVectorStore, RetrievalMode, FastEmbedSparse
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_cohere.rerank import CohereRerank
from langchain_core.tools import tool
from langchain_core.documents import Document

from app.services.ai.shared.models import get_embedding_model, get_chat_model
from app.services.ai.config import ai_config
from app.core.logger import logger


def _ensure_collection(client: QdrantClient, collection: str, dim: int) -> None:
    """Create collection with dense and sparse vectors if it doesn't exist."""
    try:
        if client.collection_exists(collection_name=collection):
            logger.info(f"✅ [RAG] Collection '{collection}' already exists")
            return
            
        logger.info(f"🏗️ [RAG] Creating new collection '{collection}' with dimension {dim}")
        
        client.create_collection(
            collection_name=collection,
            vectors_config={"dense": VectorParams(size=dim, distance=Distance.COSINE)},
            sparse_vectors_config={"sparse": SparseVectorParams(index=models.SparseIndexParams(on_disk=False))},
            optimizers_config=models.OptimizersConfigDiff(indexing_threshold=20000),
        )
        
        logger.info(f"✅ [RAG] Collection '{collection}' created successfully")
        
    except Exception as e:
        logger.error(f"❌ [RAG] Failed to ensure collection '{collection}': {str(e)}")
        raise


def _get_qdrant_store() -> QdrantVectorStore:
    """Abre colección Qdrant con HYBRID retrieval, creándola si no existe."""
    try:
        logger.info(f"🔍 [RAG] Connecting to Qdrant collection: {ai_config.qdrant_collection_name}")
        
        # Setup embeddings
        embeddings = get_embedding_model()
        sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")
        
        # Create client to check/create collection
        client = QdrantClient(
            url=ai_config.qdrant_url,
            api_key=ai_config.qdrant_api_key,
            prefer_grpc=True,
            timeout=ai_config.timeout_seconds,
        )
        
        # Ensure collection exists
        _ensure_collection(client, ai_config.qdrant_collection_name, ai_config.openai_embedding_dimension)
        
        # Now connect to the collection
        store = QdrantVectorStore.from_existing_collection(
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
        
        logger.info("✅ [RAG] Qdrant store connection established successfully")
        return store
        
    except Exception as e:
        logger.error(f"❌ [RAG] Failed to connect to Qdrant store: {str(e)}")
        raise


def _build_multiquery_retriever(store: QdrantVectorStore):
    """MMR retriever envuelto por MultiQuery para mayor recall/robustez."""
    try:
        logger.info(f"🔍 [RAG] Building MultiQuery retriever with k={ai_config.rag_retrieval_k}")
        
        base = store.as_retriever(
            search_type="mmr",
            search_kwargs={"k": ai_config.rag_retrieval_k, "fetch_k": max(12, ai_config.rag_retrieval_k * 2)},
        )
        
        llm = get_chat_model()
        retriever = MultiQueryRetriever.from_llm(retriever=base, llm=llm, include_original=True)
        
        logger.info("✅ [RAG] MultiQuery retriever built successfully")
        return retriever
        
    except Exception as e:
        logger.error(f"❌ [RAG] Failed to build MultiQuery retriever: {str(e)}")
        raise


def _compress_with_cohere(base_retriever) -> ContextualCompressionRetriever:
    """Aplica Cohere Rerank (multilingual) como compresor contextual."""
    try:
        logger.info("🔍 [RAG] Setting up Cohere rerank compressor...")
        
        compressor = CohereRerank(
            cohere_api_key=ai_config.cohere_api_key,
            model="rerank-multilingual-v3.0",   # para ES/EN
            top_n=min(8, ai_config.rag_retrieval_k * 2),
        )
        
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor, 
            base_retriever=base_retriever
        )
        
        logger.info("✅ [RAG] Cohere rerank compressor setup successfully")
        return compression_retriever
        
    except Exception as e:
        logger.error(f"❌ [RAG] Failed to setup Cohere compressor: {str(e)}")
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
def retrieve_information(query: Annotated[str, "consulta del cliente"]) -> str:
    """Recupera contexto sobre ADN (planes, precios, addons, IPTV, cobertura, proceso)."""
    try:
        logger.info(f"🔍 [RAG] Starting information retrieval for query: '{query[:100]}...'")
        
        # Step 1: Get Qdrant store
        store = _get_qdrant_store()
        
        # Step 2: Build MultiQuery retriever
        multi = _build_multiquery_retriever(store)
        
        # Step 3: Add Cohere rerank compression
        retriever = _compress_with_cohere(multi)
        
        # Step 4: Retrieve documents
        logger.info("🔍 [RAG] Executing retrieval with hybrid search + rerank...")
        docs = retriever.get_relevant_documents(query) or []
        
        logger.info(f"📊 [RAG] Retrieved {len(docs)} documents for query")
        
        if not docs:
            logger.warning("⚠️ [RAG] No documents found for query")
            return "NO_CONTEXT_AVAILABLE: La base de conocimiento está vacía o no contiene información relevante para esta consulta."
            
        # Step 5: Format and return
        formatted_context = _format_docs(docs)
        
        logger.info(f"✅ [RAG] Information retrieval completed successfully")
        return formatted_context
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ [RAG] Information retrieval failed: {error_msg}")
        
        # If it's a collection not found error, return no context signal
        if "doesn't exist" in error_msg or "not found" in error_msg.lower():
            logger.info("🏗️ [RAG] Collection doesn't exist yet, will be created on first use")
            return "NO_CONTEXT_AVAILABLE: La base de conocimiento aún no ha sido inicializada. Será creada automáticamente."
        
        # For other errors, return error signal
        return "ERROR_ACCESSING_KNOWLEDGE: No se pudo acceder a la información en este momento."
