"""
Hybrid-ready, dense-first document retriever optimized for short, structured CSV rows.
Supports multi-query expansion, compression, and enhanced metadata filtering.
"""

import asyncio
import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict

from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from langchain.retrievers.document_compressors import EmbeddingsFilter
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.logger import logger
from app.services.ai.config import ai_config
from app.services.ai.rag.schemas import (
    RetrieverConfig, RetrievalResult, DocumentChunk, RetrievalMethod,
    MultiQueryConfig, CompressionConfig
)


class MultiQueryExpander:
    """Handles multi-query expansion for improved retrieval."""
    
    def __init__(self, config: MultiQueryConfig):
        self.config = config
        
    def expand_query(self, query: str) -> List[str]:
        """
        Expand a query into multiple variants for better retrieval.
        
        Args:
            query: Original query
            
        Returns:
            List of expanded queries
        """
        expanded_queries = [query]
        
        # Normalize accents if enabled
        if self.config.enable_accent_normalization:
            normalized_query = self._normalize_accents(query)
            if normalized_query != query:
                expanded_queries.append(normalized_query)
        
        # Expand synonyms
        if self.config.enable_synonym_expansion:
            synonym_queries = self._expand_synonyms(query)
            expanded_queries.extend(synonym_queries)
        
        # Expand numeric patterns
        if self.config.enable_numeric_expansion:
            numeric_queries = self._expand_numeric_patterns(query)
            expanded_queries.extend(numeric_queries)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for q in expanded_queries:
            if q.lower() not in seen:
                seen.add(q.lower())
                unique_queries.append(q)
        
        # Limit to max_expanded_queries
        return unique_queries[:self.config.max_expanded_queries]
    
    def _normalize_accents(self, text: str) -> str:
        """Normalize Spanish accents for better matching."""
        accent_map = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ü': 'u', 'ñ': 'n', 'Á': 'A', 'É': 'E', 'Í': 'I',
            'Ó': 'O', 'Ú': 'U', 'Ü': 'U', 'Ñ': 'N'
        }
        
        for accented, plain in accent_map.items():
            text = text.replace(accented, plain)
        
        return text
    
    def _expand_synonyms(self, query: str) -> List[str]:
        """Expand query using Spanish synonyms."""
        expanded = []
        query_lower = query.lower()
        
        for word, synonyms in self.config.spanish_synonyms.items():
            if word in query_lower:
                for synonym in synonyms:
                    expanded_query = query_lower.replace(word, synonym)
                    if expanded_query != query_lower:
                        expanded.append(expanded_query)
        
        return expanded
    
    def _expand_numeric_patterns(self, query: str) -> List[str]:
        """Expand numeric patterns in the query."""
        expanded = []
        
        for pattern, templates in self.config.numeric_patterns.items():
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                for template in templates:
                    try:
                        expanded_text = template.format(*groups)
                        expanded_query = query[:match.start()] + expanded_text + query[match.end():]
                        expanded.append(expanded_query)
                    except (IndexError, KeyError):
                        continue
        
        return expanded


class ResultCompressor:
    """Handles result compression and reordering."""
    
    def __init__(self, config: CompressionConfig, embeddings: OpenAIEmbeddings):
        self.config = config
        self.embeddings = embeddings
        
    async def compress_results(
        self, 
        documents: List[Document], 
        query: str
    ) -> List[Document]:
        """
        Compress and reorder retrieval results.
        
        Args:
            documents: Retrieved documents
            query: Original query
            
        Returns:
            Compressed and reordered documents
        """
        if not documents:
            return documents
        
        # Apply embeddings filter
        if self.config.similarity_threshold > 0:
            documents = await self._filter_by_similarity(documents, query)
        
        # Apply reordering if enabled
        if self.config.enable_reordering and len(documents) > self.config.reorder_window:
            documents = await self._reorder_documents(documents, query)
        
        # Limit to max chunks
        return documents[:self.config.max_chunks]
    
    async def _filter_by_similarity(
        self, 
        documents: List[Document], 
        query: str
    ) -> List[Document]:
        """Filter documents by similarity threshold."""
        try:
            # Create embeddings filter
            embeddings_filter = EmbeddingsFilter(
                embeddings=self.embeddings,
                similarity_threshold=self.config.similarity_threshold
            )
            
            # Filter documents
            filtered_docs = await asyncio.to_thread(
                embeddings_filter.compress_documents,
                documents,
                query
            )
            
            return filtered_docs
            
        except Exception as e:
            logger.warning(f"Error in similarity filtering: {str(e)}")
            return documents
    
    async def _reorder_documents(
        self, 
        documents: List[Document], 
        query: str
    ) -> List[Document]:
        """Reorder documents for better context flow."""
        try:
            # Simple reordering: prioritize documents with better metadata matches
            def reorder_score(doc: Document) -> float:
                score = 0.0
                metadata = doc.metadata
                
                # Boost FAQ entries
                if metadata.get("is_faq", False):
                    score += 0.3
                
                # Boost entries with prices for price queries
                if "precio" in query.lower() and metadata.get("price_text"):
                    score += 0.2
                
                # Boost entries with contact info for contact queries
                if any(word in query.lower() for word in ["contacto", "teléfono", "número"]):
                    if metadata.get("contact_value"):
                        score += 0.2
                
                # Boost entries with URLs for service queries
                if metadata.get("url"):
                    score += 0.1
                
                return score
            
            # Sort by reorder score (descending)
            reordered = sorted(documents, key=reorder_score, reverse=True)
            
            return reordered
            
        except Exception as e:
            logger.warning(f"Error in document reordering: {str(e)}")
            return documents


class HybridRetriever:
    """Hybrid-ready, dense-first retriever with multi-query expansion and compression."""
    
    def __init__(self, config: RetrieverConfig):
        self.config = config
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=ai_config.openai_api_key,
            model=ai_config.openai_embedding_model,
            dimensions=ai_config.openai_embedding_dimension
        )
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            url=ai_config.qdrant_url,
            api_key=ai_config.qdrant_api_key
        )
        
        # Initialize vector store
        self.vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=ai_config.qdrant_collection_name,
            embedding=self.embeddings
        )
        
        # Initialize components
        self.multi_query_expander = MultiQueryExpander(
            MultiQueryConfig(max_expanded_queries=config.max_expanded_queries)
        )
        
        self.compressor = ResultCompressor(
            CompressionConfig(
                similarity_threshold=config.compression_threshold,
                max_chunks=config.max_final_chunks
            ),
            self.embeddings
        )
        
        # Store vector store for direct access
        self.vector_store = self.vector_store
    
    def _build_search_kwargs(self) -> Dict[str, Any]:
        """Build search kwargs with filters and parameters."""
        search_kwargs = {
            "k": self.config.k,
            "score_threshold": self.config.score_threshold
        }
        
        # Note: ef parameter removed due to Qdrant client compatibility issues
        # The parameter is not essential for basic retrieval functionality
        
        # Build filters
        filters = self._build_filters()
        if filters:
            search_kwargs["filter"] = filters
        
        # Add any additional search kwargs
        search_kwargs.update(self.config.search_kwargs)
        
        return search_kwargs
    
    def _build_filters(self) -> Optional[models.Filter]:
        """Build Qdrant filters based on configuration."""
        conditions = []
        
        # Required filters
        if self.config.tenant_id:
            conditions.append(
                models.FieldCondition(
                    key="tenant_id",
                    match=models.MatchValue(value=self.config.tenant_id)
                )
            )
        
        if self.config.locale:
            conditions.append(
                models.FieldCondition(
                    key="locale",
                    match=models.MatchValue(value=self.config.locale)
                )
            )
        
        # Intent-based filters (optional)
        intent_filters = self._build_intent_filters()
        if intent_filters:
            conditions.extend(intent_filters)
        
        if not conditions:
            return None
        
        return models.Filter(must=conditions)
    
    def _build_intent_filters(self) -> List[models.FieldCondition]:
        """Build intent-based filters for better precision."""
        # This would be called with the actual query to add section/tag filters
        # For now, return empty list - will be implemented in retrieval method
        return []
    
    async def aget_relevant_documents(self, query: str) -> List[Document]:
        """
        Asynchronously retrieve relevant documents with multi-query expansion.
        
        Args:
            query: Search query
            
        Returns:
            List of relevant documents
        """
        start_time = datetime.now()
        
        try:
            # Expand query if enabled
            if self.config.enable_multi_query:
                expanded_queries = self.multi_query_expander.expand_query(query)
                logger.info(f"Expanded query '{query}' into {len(expanded_queries)} variants")
            else:
                expanded_queries = [query]
            
            # Retrieve documents for each expanded query
            all_documents = []
            all_scores = []
            
            for expanded_query in expanded_queries:
                # Update intent filters for this query
                self._update_intent_filters(expanded_query)
                
                # Retrieve documents
                results = await asyncio.to_thread(
                    self.vector_store.similarity_search_with_score,
                    expanded_query,
                    **self._build_search_kwargs()
                )
                
                all_documents.extend([doc for doc, _ in results])
                all_scores.extend([score for _, score in results])
            
            # Remove duplicates while preserving order
            seen_doc_ids = set()
            unique_documents = []
            unique_scores = []
            
            for doc, score in zip(all_documents, all_scores):
                doc_id = doc.metadata.get("doc_id", doc.page_content[:50])
                if doc_id not in seen_doc_ids:
                    seen_doc_ids.add(doc_id)
                    unique_documents.append(doc)
                    unique_scores.append(score)
            
            # Apply compression if enabled
            if self.config.enable_compression:
                unique_documents = await self.compressor.compress_results(
                    unique_documents, query
                )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(
                f"Retrieved {len(unique_documents)} documents for query '{query[:50]}...' "
                f"in {processing_time:.2f}ms"
            )
            
            return unique_documents
            
        except Exception as e:
            logger.error(f"Error retrieving documents for query '{query}': {str(e)}")
            return []
    
    def _update_intent_filters(self, query: str):
        """Update intent-based filters based on query content."""
        # This method would update the retriever's filters based on query keywords
        # Implementation would be called before each retrieval
        pass
    
    async def get_retrieval_result(self, query: str) -> RetrievalResult:
        """
        Get comprehensive retrieval result with metadata.
        
        Args:
            query: Search query
            
        Returns:
            RetrievalResult with documents and metadata
        """
        start_time = datetime.now()
        
        try:
            # Get expanded queries for logging
            if self.config.enable_multi_query:
                expanded_queries = self.multi_query_expander.expand_query(query)
            else:
                expanded_queries = [query]
            
            # Retrieve documents
            documents = await self.aget_relevant_documents(query)
            
            # Convert to DocumentChunk format
            chunks = []
            scores = []
            metadata_overrides = 0
            
            for doc in documents:
                try:
                    chunk_data = doc.metadata.copy()
                    chunk_data["content"] = doc.page_content
                    
                    # Handle datetime fields
                    if "updated_at" in chunk_data and isinstance(chunk_data["updated_at"], str):
                        chunk_data["updated_at"] = datetime.fromisoformat(
                            chunk_data["updated_at"].replace("Z", "+00:00")
                        )
                    
                    # Check for metadata overrides
                    if chunk_data.get("retrieval_score", 0) < self.config.score_threshold:
                        metadata_overrides += 1
                    
                    chunk = DocumentChunk(**chunk_data)
                    chunks.append(chunk)
                    scores.append(chunk_data.get("retrieval_score", 0.0))
                    
                except Exception as e:
                    logger.warning(f"Could not convert document to chunk: {e}")
                    continue
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return RetrievalResult(
                documents=chunks,
                scores=scores,
                query=query,
                expanded_queries=expanded_queries,
                total_found=len(chunks),
                retrieval_time_ms=int(processing_time),
                method=self.config.method,
                filters_applied=self._build_filters().__dict__ if self._build_filters() else {},
                threshold_used=self.config.score_threshold,
                metadata_overrides=metadata_overrides
            )
            
        except Exception as e:
            logger.error(f"Error in get_retrieval_result: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return RetrievalResult(
                documents=[],
                scores=[],
                query=query,
                expanded_queries=[query],
                total_found=0,
                retrieval_time_ms=int(processing_time),
                method=self.config.method,
                filters_applied={},
                threshold_used=self.config.score_threshold,
                metadata_overrides=0
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check retriever health and connectivity."""
        try:
            # Test a simple query
            test_result = await self.aget_relevant_documents("test query")
            
            return {
                "status": "healthy",
                "collection_name": ai_config.qdrant_collection_name,
                "embedding_model": ai_config.openai_embedding_model,
                "test_query_results": len(test_result),
                "config": self.config.model_dump()
            }
            
        except Exception as e:
            logger.error(f"Retriever health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "config": self.config.model_dump()
            }


def build_retriever(
    tenant_id: Optional[str] = None,
    locale: Optional[str] = "es_CR",
    k: int = 10,
    score_threshold: Optional[float] = 0.20,
    method: RetrievalMethod = RetrievalMethod.DENSE,
    enable_multi_query: bool = True,
    enable_compression: bool = True
) -> HybridRetriever:
    """
    Build a configured hybrid retriever instance.
    
    Args:
        tenant_id: Filter by tenant ID
        locale: Filter by locale
        k: Number of documents to retrieve
        score_threshold: Minimum similarity score
        method: Retrieval method
        enable_multi_query: Enable multi-query expansion
        enable_compression: Enable result compression
        
    Returns:
        Configured retriever instance
    """
    config = RetrieverConfig(
        k=k,
        score_threshold=score_threshold,
        tenant_id=tenant_id,
        locale=locale,
        method=method,
        enable_multi_query=enable_multi_query,
        enable_compression=enable_compression
    )
    
    return HybridRetriever(config)


# Convenience function for default retriever
def get_default_retriever(
    tenant_id: str = "default", 
    locale: str = "es_CR"
) -> HybridRetriever:
    """Get a default retriever with common settings."""
    return build_retriever(
        tenant_id=tenant_id,
        locale=locale,
        k=ai_config.rag_retrieval_k
    )


# Legacy class removed - use HybridRetriever directly
