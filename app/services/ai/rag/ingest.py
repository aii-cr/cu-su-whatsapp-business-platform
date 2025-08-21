"""
Document ingestion with semantic chunking for Qdrant vector store.
Processes CSV data and creates parent-child document relationships.
"""

import asyncio
import hashlib
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import uuid4

from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.logger import logger
from app.services.ai.config import ai_config
from app.services.ai.rag.schemas import DocumentChunk, IngestionResult


class DocumentIngester:
    """Handles document ingestion with semantic chunking."""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=ai_config.openai_api_key,
            model=ai_config.openai_embedding_model,
            dimensions=ai_config.openai_embedding_dimension
        )
        
        self.qdrant_client = QdrantClient(
            url=ai_config.qdrant_url,
            api_key=ai_config.qdrant_api_key
        )
        
        self.semantic_chunker = SemanticChunker(
            embeddings=self.embeddings,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=95
        )
        
    async def ingest_csv_dataset(
        self, 
        csv_path: str, 
        tenant_id: str = "default",
        locale: str = "es"
    ) -> IngestionResult:
        """
        Ingest CSV dataset with semantic chunking.
        
        Args:
            csv_path: Path to CSV file
            tenant_id: Tenant identifier for multi-tenancy
            locale: Language locale (es/en)
            
        Returns:
            IngestionResult with operation details
        """
        start_time = datetime.now()
        logger.info(f"Starting CSV ingestion from {csv_path}")
        
        try:
            # Load CSV data
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded {len(df)} rows from CSV")
            
            # Ensure collection exists
            await self._ensure_collection_exists()
            
            # Process documents
            all_chunks = []
            documents_processed = 0
            
            for idx, row in df.iterrows():
                try:
                    chunks = await self._process_document_row(row, tenant_id, locale, idx)
                    all_chunks.extend(chunks)
                    documents_processed += 1
                    
                    if documents_processed % 10 == 0:
                        logger.info(f"Processed {documents_processed} documents...")
                        
                except Exception as e:
                    logger.error(f"Error processing row {idx}: {str(e)}")
                    continue
            
            # Store chunks in Qdrant
            chunks_stored = await self._store_chunks(all_chunks)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            result = IngestionResult(
                success=True,
                documents_processed=documents_processed,
                chunks_created=len(all_chunks),
                chunks_stored=chunks_stored,
                processing_time_ms=int(processing_time),
                collection_name=ai_config.qdrant_collection_name
            )
            
            logger.info(f"Ingestion completed: {result.model_dump()}")
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Ingestion failed: {str(e)}")
            
            return IngestionResult(
                success=False,
                documents_processed=0,
                chunks_created=0,
                chunks_stored=0,
                processing_time_ms=int(processing_time),
                errors=[str(e)],
                collection_name=ai_config.qdrant_collection_name
            )
    
    async def _process_document_row(
        self, 
        row: pd.Series, 
        tenant_id: str, 
        locale: str, 
        row_idx: int
    ) -> List[DocumentChunk]:
        """Process a single CSV row into semantic chunks."""
        
        # Extract content and metadata from CSV row
        content = self._extract_content_from_row(row)
        if not content.strip():
            return []
        
        # Generate version hash for content
        version_hash = hashlib.md5(content.encode()).hexdigest()
        
        # Create semantic chunks
        text_chunks = await asyncio.to_thread(
            self.semantic_chunker.split_text, content
        )
        
        chunks = []
        for chunk_idx, chunk_text in enumerate(text_chunks):
            chunk = DocumentChunk(
                content=chunk_text.strip(),
                source=f"csv_row_{row_idx}",
                section=row.get("section", "general"),
                tenant_id=tenant_id,
                locale=locale,
                version_hash=version_hash,
                updated_at=datetime.now(timezone.utc),
                pii=False,  # Assume no PII in knowledge base
                chunk_index=chunk_idx
            )
            chunks.append(chunk)
        
        return chunks
    
    def _extract_content_from_row(self, row: pd.Series) -> str:
        """Extract and combine relevant content from CSV row."""
        content_parts = []
        
        # Common CSV column names to check
        content_columns = [
            "content", "text", "description", "body", "message",
            "question", "answer", "info", "details"
        ]
        
        for col in content_columns:
            if col in row.index and pd.notna(row[col]):
                content_parts.append(str(row[col]))
        
        # If no content columns found, combine all non-null text columns
        if not content_parts:
            for col, value in row.items():
                if isinstance(value, str) and pd.notna(value) and value.strip():
                    content_parts.append(f"{col}: {value}")
        
        return "\n".join(content_parts)
    
    async def _ensure_collection_exists(self):
        """Ensure Qdrant collection exists with proper configuration."""
        collection_name = ai_config.qdrant_collection_name
        
        try:
            # Check if collection exists
            collections = await asyncio.to_thread(
                self.qdrant_client.get_collections
            )
            
            existing_names = [c.name for c in collections.collections]
            
            if collection_name not in existing_names:
                # Create collection
                await asyncio.to_thread(
                    self.qdrant_client.create_collection,
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=ai_config.openai_embedding_dimension,
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {collection_name}")
            else:
                logger.info(f"Qdrant collection exists: {collection_name}")
                
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {str(e)}")
            raise
    
    async def _store_chunks(self, chunks: List[DocumentChunk]) -> int:
        """Store document chunks in Qdrant vector store."""
        if not chunks:
            return 0
        
        try:
            # Prepare documents for vector store
            texts = [chunk.content for chunk in chunks]
            metadatas = [chunk.model_dump(exclude={"content"}) for chunk in chunks]
            ids = [str(uuid4()) for _ in chunks]
            
            # Create vector store instance
            vector_store = QdrantVectorStore(
                client=self.qdrant_client,
                collection_name=ai_config.qdrant_collection_name,
                embedding=self.embeddings
            )
            
            # Add documents in batches to avoid memory issues
            batch_size = 50
            total_stored = 0
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_metadatas = metadatas[i:i + batch_size]
                batch_ids = ids[i:i + batch_size]
                
                await asyncio.to_thread(
                    vector_store.add_texts,
                    texts=batch_texts,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
                
                total_stored += len(batch_texts)
                logger.info(f"Stored batch: {total_stored}/{len(texts)} chunks")
            
            return total_stored
            
        except Exception as e:
            logger.error(f"Error storing chunks in Qdrant: {str(e)}")
            raise


async def ingest_documents(
    csv_path: Optional[str] = None,
    tenant_id: str = "default",
    locale: str = "es"
) -> IngestionResult:
    """
    Convenience function to ingest documents.
    
    Args:
        csv_path: Path to CSV file (defaults to the golden dataset)
        tenant_id: Tenant identifier
        locale: Language locale
        
    Returns:
        IngestionResult with operation details
    """
    if csv_path is None:
        csv_path = "app/services/ai/datasets/adn_rag_base_full_v1_3.csv"
    
    ingester = DocumentIngester()
    return await ingester.ingest_csv_dataset(csv_path, tenant_id, locale)


async def check_collection_health() -> Dict[str, Any]:
    """
    Check the health and status of the Qdrant collection.
    
    Returns:
        Dict with collection health information
    """
    try:
        client = QdrantClient(
            url=ai_config.qdrant_url,
            api_key=ai_config.qdrant_api_key
        )
        
        collection_name = ai_config.qdrant_collection_name
        
        # Get collection info
        collection_info = await asyncio.to_thread(
            client.get_collection, collection_name
        )
        
        # Get collection statistics
        collection_stats = await asyncio.to_thread(
            client.get_collection, collection_name
        )
        
        return {
            "collection_exists": True,
            "collection_name": collection_name,
            "vectors_count": collection_info.vectors_count,
            "indexed_vectors_count": collection_info.indexed_vectors_count,
            "points_count": collection_info.points_count,
            "status": collection_info.status.value,
            "config": {
                "vector_size": collection_info.config.params.vectors.size,
                "distance": collection_info.config.params.vectors.distance.value
            }
        }
        
    except UnexpectedResponse as e:
        if "doesn't exist" in str(e).lower():
            return {
                "collection_exists": False,
                "collection_name": ai_config.qdrant_collection_name,
                "error": "Collection does not exist"
            }
        else:
            logger.error(f"Error checking collection health: {str(e)}")
            return {
                "collection_exists": False,
                "collection_name": ai_config.qdrant_collection_name,
                "error": str(e)
            }
    except Exception as e:
        logger.error(f"Error checking collection health: {str(e)}")
        return {
            "collection_exists": False,
            "collection_name": ai_config.qdrant_collection_name,
            "error": str(e)
        }
