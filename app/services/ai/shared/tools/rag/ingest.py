"""
New hybrid document ingestion for JSONL files.
Implements dense + BM25 sparse vectors using Qdrant hybrid retrieval.
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, SparseVectorParams
from langchain_qdrant import QdrantVectorStore, RetrievalMode, FastEmbedSparse
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.core.logger import logger
from app.services.ai.config import ai_config
from .schemas import IngestionResult


def load_jsonl_documents(paths: list[str]) -> List[Document]:
    """Load JSONL files to Document(page_content=text, metadata=metadata)."""
    try:
        logger.info(f"📂 [JSONL] Loading documents from {len(paths)} JSONL files")
        
        docs: List[Document] = []
        
        for file_idx, p in enumerate(paths, 1):
            path = Path(p)
            
            if not path.exists():
                logger.warning(f"⚠️ [JSONL] File {file_idx} not found: {p}")
                continue
                
            logger.info(f"📂 [JSONL] Processing file {file_idx}/{len(paths)}: {path.name}")
            
            file_docs = 0
            with path.open("r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                        
                    try:
                        obj: Dict[str, Any] = json.loads(line)
                        text = obj.get("text", "")
                        meta = obj.get("metadata", {})
                        
                        if text:  # Only add documents with content
                            docs.append(Document(page_content=text, metadata=meta))
                            file_docs += 1
                        else:
                            logger.debug(f"📂 [JSONL] Skipping empty text at line {line_num} in {path.name}")
                            
                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️ [JSONL] Invalid JSON at line {line_num} in {path.name}: {str(e)}")
                        continue
                        
            logger.info(f"✅ [JSONL] Loaded {file_docs} documents from {path.name}")
            
        total_docs = len(docs)
        logger.info(f"🎉 [JSONL] Total documents loaded: {total_docs}")
        
        return docs
        
    except Exception as e:
        logger.error(f"❌ [JSONL] Failed to load JSONL documents: {str(e)}")
        return []


def get_embedding_model() -> OpenAIEmbeddings:
    """Get the dense embedding model according to configuration."""
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


def ensure_collection(client: QdrantClient, collection: str, dim: int) -> None:
    """Create collection with dense and sparse vectors if it doesn't exist."""
    try:
        if client.collection_exists(collection_name=collection):
            logger.info(f"✅ [INGEST] Collection '{collection}' already exists")
            return
            
        logger.info(f"🏗️ [INGEST] Creating new collection '{collection}' with dimension {dim}")
        
        client.create_collection(
            collection_name=collection,
            vectors_config={"dense": VectorParams(size=dim, distance=Distance.COSINE)},
            sparse_vectors_config={"sparse": SparseVectorParams(index=models.SparseIndexParams(on_disk=False))},
            optimizers_config=models.OptimizersConfigDiff(indexing_threshold=20000),
        )
        
        logger.info(f"✅ [INGEST] Collection '{collection}' created successfully")
        
    except Exception as e:
        logger.error(f"❌ [INGEST] Failed to ensure collection '{collection}': {str(e)}")
        raise


def ingest_jsonl(paths: List[str], batch_size: int = 200) -> QdrantVectorStore:
    """Ingest JSONL files to Qdrant (HYBRID)."""
    try:
        logger.info(f"🚀 [INGEST] Starting hybrid JSONL ingestion with {len(paths)} files")
        logger.info(f"📁 [INGEST] Input files: {paths}")
        
        # Step 1: Setup Qdrant client
        logger.info("🔗 [INGEST] Connecting to Qdrant...")
        client = QdrantClient(
            url=ai_config.qdrant_url,
            api_key=ai_config.qdrant_api_key,
            prefer_grpc=True,
            timeout=ai_config.timeout_seconds,
        )
        
        # Step 2: Setup embeddings
        logger.info("🔤 [INGEST] Setting up embeddings...")
        embeddings = get_embedding_model()
        sparse = FastEmbedSparse(model_name="Qdrant/bm25")  # BM25-like

        # Step 3: Ensure collection exists
        logger.info(f"🏗️ [INGEST] Ensuring collection '{ai_config.qdrant_collection_name}' exists...")
        ensure_collection(client, ai_config.qdrant_collection_name, ai_config.openai_embedding_dimension)

        # Step 4: Load and split documents
        logger.info("📄 [INGEST] Loading JSONL documents...")
        docs = load_jsonl_documents(paths)
        logger.info(f"📄 [INGEST] Loaded {len(docs)} documents")
        
        logger.info("✂️ [INGEST] Splitting documents into chunks...")
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
        chunks = splitter.split_documents(docs)
        logger.info(f"✂️ [INGEST] Created {len(chunks)} chunks")

        # Step 5: Setup vector store
        logger.info("🏪 [INGEST] Setting up hybrid vector store...")
        store = QdrantVectorStore(
            client=client,
            collection_name=ai_config.qdrant_collection_name,
            embedding=embeddings,
            sparse_embedding=sparse,
            retrieval_mode=RetrievalMode.HYBRID,  # requires Qdrant >=1.10.0
            vector_name="dense",
            sparse_vector_name="sparse",
        )

        # Step 6: Ingest documents in batches
        logger.info(f"📥 [INGEST] Ingesting {len(chunks)} chunks in batches of {batch_size}...")
        
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        for i in range(0, len(chunks), batch_size):
            batch_num = (i // batch_size) + 1
            batch_chunks = chunks[i : i + batch_size]
            
            logger.info(f"📥 [INGEST] Processing batch {batch_num}/{total_batches} ({len(batch_chunks)} chunks)")
            store.add_documents(documents=batch_chunks)
            logger.info(f"✅ [INGEST] Batch {batch_num}/{total_batches} completed")

        logger.info("🎉 [INGEST] Hybrid JSONL ingestion completed successfully")
        return store
        
    except Exception as e:
        logger.error(f"❌ [INGEST] Hybrid JSONL ingestion failed: {str(e)}")
        raise


async def ingest_documents() -> IngestionResult:
    """
    Ingest JSONL documents using the new hybrid approach.
    
    Returns:
        IngestionResult: Result of the ingestion process
    """
    try:
        logger.info("🔄 Starting hybrid document ingestion...")
        
        # Define JSONL paths
        jsonl_paths = [
            "/home/sa/dev/cu-su-backend/RAG_data/adn_master_company.jsonl",
            "/home/sa/dev/cu-su-backend/RAG_data/adn_iptv_channels.jsonl"
        ]
        
        # Check that files exist
        existing_paths = []
        for path in jsonl_paths:
            if Path(path).exists():
                existing_paths.append(path)
                logger.info(f"✅ Found JSONL file: {path}")
            else:
                logger.warning(f"❌ JSONL file not found: {path}")
        
        if not existing_paths:
            logger.error("No JSONL files found for ingestion")
            return IngestionResult(
                success=False,
                documents_processed=0,
                chunks_stored=0,
                errors=["No JSONL files found"],
                processing_time_seconds=0
            )
        
        start_time = datetime.now(timezone.utc)
        
        # Use the new hybrid ingestion system
        store = ingest_jsonl_hybrid(existing_paths)
        
        # Get collection info for result metrics
        from qdrant_client import QdrantClient
        client = QdrantClient(
            url=ai_config.qdrant_url,
            api_key=ai_config.qdrant_api_key,
            prefer_grpc=True
        )
        
        collection_info = client.get_collection(ai_config.qdrant_collection_name)
        vectors_count = collection_info.vectors_count
        
        end_time = datetime.now(timezone.utc)
        processing_time = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ Hybrid ingestion completed: {vectors_count} vectors stored")
        
        return IngestionResult(
            success=True,
            documents_processed=len(existing_paths),
            chunks_stored=vectors_count,
            errors=[],
            processing_time_seconds=processing_time
        )
        
    except Exception as e:
        logger.error(f"❌ Hybrid ingestion failed: {str(e)}")
        return IngestionResult(
            success=False,
            documents_processed=0,
            chunks_stored=0,
            errors=[str(e)],
            processing_time_seconds=0
        )


async def check_collection_health() -> Dict[str, Any]:
    """
    Check the health of the Qdrant collection.
    
    Returns:
        Dict containing collection health information
    """
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(
            url=ai_config.qdrant_url,
            api_key=ai_config.qdrant_api_key,
            prefer_grpc=True
        )
        
        collection_exists = client.collection_exists(ai_config.qdrant_collection_name)
        
        if not collection_exists:
            return {
                "collection_exists": False,
                "vectors_count": 0,
                "status": "not_found"
            }
        
        collection_info = client.get_collection(ai_config.qdrant_collection_name)
        
        return {
            "collection_exists": True,
            "vectors_count": collection_info.vectors_count,
            "status": "healthy" if collection_info.vectors_count > 0 else "empty"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to check collection health: {str(e)}")
        return {
            "collection_exists": False,
            "vectors_count": 0,
            "status": "error",
            "error": str(e)
        }


def ensure_collection(client: QdrantClient, collection: str, dim: int) -> None:
    """Crea colección con vector denso y esparso si no existe."""
    try:
        if client.collection_exists(collection_name=collection):
            logger.info(f"✅ [INGEST] Collection '{collection}' already exists")
            return
            
        logger.info(f"🏗️ [INGEST] Creating new collection '{collection}' with dimension {dim}")
        
        client.create_collection(
            collection_name=collection,
            vectors_config={"dense": VectorParams(size=dim, distance=Distance.COSINE)},
            sparse_vectors_config={"sparse": SparseVectorParams(index=models.SparseIndexParams(on_disk=False))},
            optimizers_config=models.OptimizersConfigDiff(indexing_threshold=20000),
        )
        
        logger.info(f"✅ [INGEST] Collection '{collection}' created successfully")
        
    except Exception as e:
        logger.error(f"❌ [INGEST] Failed to ensure collection '{collection}': {str(e)}")
        raise


def ingest_jsonl_hybrid(paths: List[str], batch_size: int = 200) -> QdrantVectorStore:
    """Ingesta JSONL en Qdrant (HYBRID) - nueva implementación mejorada."""
    try:
        logger.info(f"🚀 [INGEST] Starting hybrid JSONL ingestion with {len(paths)} files")
        logger.info(f"📁 [INGEST] Input files: {paths}")
        
        # Step 1: Setup Qdrant client
        logger.info("🔗 [INGEST] Connecting to Qdrant...")
        client = QdrantClient(
            url=ai_config.qdrant_url,
            api_key=ai_config.qdrant_api_key,
            prefer_grpc=True,
            timeout=ai_config.timeout_seconds,
        )
        
        # Step 2: Setup embeddings
        logger.info("🔤 [INGEST] Setting up embeddings...")
        from app.services.ai.shared.models import get_embedding_model
        embeddings = get_embedding_model()
        sparse = FastEmbedSparse(model_name="Qdrant/bm25")  # BM25-like

        # Step 3: Ensure collection exists
        logger.info(f"🏗️ [INGEST] Ensuring collection '{ai_config.qdrant_collection_name}' exists...")
        ensure_collection(client, ai_config.qdrant_collection_name, ai_config.openai_embedding_dimension)

        # Step 4: Load and split documents
        logger.info("📄 [INGEST] Loading JSONL documents...")
        docs = load_jsonl_documents(paths)
        logger.info(f"📄 [INGEST] Loaded {len(docs)} documents")
        
        logger.info("✂️ [INGEST] Splitting documents into chunks...")
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
        chunks = splitter.split_documents(docs)
        logger.info(f"✂️ [INGEST] Created {len(chunks)} chunks")

        # Step 5: Setup vector store
        logger.info("🏪 [INGEST] Setting up hybrid vector store...")
        store = QdrantVectorStore(
            client=client,
            collection_name=ai_config.qdrant_collection_name,
            embedding=embeddings,
            sparse_embedding=sparse,
            retrieval_mode=RetrievalMode.HYBRID,  # requiere Qdrant >=1.10.0
            vector_name="dense",
            sparse_vector_name="sparse",
        )

        # Step 6: Ingest documents in batches
        logger.info(f"📥 [INGEST] Ingesting {len(chunks)} chunks in batches of {batch_size}...")
        
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        for i in range(0, len(chunks), batch_size):
            batch_num = (i // batch_size) + 1
            batch_chunks = chunks[i : i + batch_size]
            
            logger.info(f"📥 [INGEST] Processing batch {batch_num}/{total_batches} ({len(batch_chunks)} chunks)")
            store.add_documents(documents=batch_chunks)
            logger.info(f"✅ [INGEST] Batch {batch_num}/{total_batches} completed")

        logger.info("🎉 [INGEST] Hybrid JSONL ingestion completed successfully")
        return store
        
    except Exception as e:
        logger.error(f"❌ [INGEST] Hybrid JSONL ingestion failed: {str(e)}")
        raise
