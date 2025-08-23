# NEW CODE
"""
Ingesta híbrida (denso + BM25) a Qdrant desde JSONL.
"""

from __future__ import annotations
from typing import List
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, SparseVectorParams
from langchain_qdrant import QdrantVectorStore, RetrievalMode, FastEmbedSparse
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .jsonl_loader import load_jsonl_documents
from ..models import get_embedding_model
from app.services.ai.config import ai_config
from app.core.logger import logger


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


def ingest_jsonl(paths: List[str], batch_size: int = 200) -> QdrantVectorStore:
    """Ingesta JSONL en Qdrant (HYBRID)."""
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
        ensure_collection(client, ai_config.qdrant_collection_name, embeddings.dimension)

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
