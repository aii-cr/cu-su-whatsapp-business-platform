#!/usr/bin/env python3
"""
Utility script to fix Qdrant collection dimension mismatch.
This script recreates the collection with the correct dimensions for text-embedding-3-large (3072).
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, SparseVectorParams
from app.core.config import settings
from app.core.logger import logger


async def fix_qdrant_dimensions():
    """Fix the Qdrant collection dimension mismatch."""
    try:
        logger.info("🔧 Starting Qdrant dimension fix...")
        
        # Connect to Qdrant
        client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            prefer_grpc=True
        )
        
        collection_name = settings.QDRANT_COLLECTION_NAME
        
        # Check if collection exists
        if client.collection_exists(collection_name=collection_name):
            logger.info(f"📦 Found existing collection: {collection_name}")
            
            # Get collection info
            collection_info = client.get_collection(collection_name)
            logger.info(f"📊 Current collection info: {collection_info}")
            
            # Check if we need to recreate
            vectors_config = collection_info.config.params.vectors
            if hasattr(vectors_config, 'size'):
                current_dim = vectors_config.size
                logger.info(f"🔍 Current dimension: {current_dim}")
                
                if current_dim == 3072:
                    logger.info("✅ Collection already has correct dimensions (3072)")
                    return
                else:
                    logger.info(f"⚠️  Dimension mismatch: {current_dim} != 3072")
            else:
                logger.info("⚠️  Could not determine current dimensions")
            
            # Ask for confirmation
            response = input(f"\n❓ Do you want to delete and recreate collection '{collection_name}'? (y/N): ")
            if response.lower() != 'y':
                logger.info("❌ Operation cancelled by user")
                return
            
            # Delete existing collection
            logger.info(f"🗑️  Deleting collection: {collection_name}")
            client.delete_collection(collection_name=collection_name)
            logger.info("✅ Collection deleted")
        
        # Create new collection with correct dimensions
        logger.info(f"🏗️  Creating new collection '{collection_name}' with 3072 dimensions")
        
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "dense": VectorParams(
                    size=3072,  # text-embedding-3-large dimension
                    distance=Distance.COSINE
                )
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(
                    index={"on_disk": False}
                )
            },
            optimizers_config={"indexing_threshold": 20000}
        )
        
        logger.info("✅ Collection created successfully with correct dimensions")
        
        # Verify the collection
        collection_info = client.get_collection(collection_name=collection_name)
        logger.info(f"✅ Verification: {collection_info}")
        
        logger.info("🎉 Qdrant dimension fix completed successfully!")
        logger.info("💡 You may need to re-ingest your documents now.")
        
    except Exception as e:
        logger.error(f"❌ Failed to fix Qdrant dimensions: {str(e)}")
        raise


async def check_collection_status():
    """Check the current status of the Qdrant collection."""
    try:
        logger.info("🔍 Checking Qdrant collection status...")
        
        client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            prefer_grpc=True
        )
        
        collection_name = settings.QDRANT_COLLECTION_NAME
        
        if not client.collection_exists(collection_name=collection_name):
            logger.info(f"❌ Collection '{collection_name}' does not exist")
            return
        
        collection_info = client.get_collection(collection_name=collection_name)
        logger.info(f"📊 Collection info: {collection_info}")
        
        vectors_config = collection_info.config.params.vectors
        if hasattr(vectors_config, 'size'):
            logger.info(f"🔍 Vector dimension: {vectors_config.size}")
            if vectors_config.size == 3072:
                logger.info("✅ Dimensions are correct for text-embedding-3-large")
            else:
                logger.info(f"⚠️  Dimensions are incorrect. Expected: 3072, Got: {vectors_config.size}")
        else:
            logger.info("⚠️  Could not determine vector dimensions")
        
    except Exception as e:
        logger.error(f"❌ Failed to check collection status: {str(e)}")
        raise


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        asyncio.run(check_collection_status())
    else:
        asyncio.run(fix_qdrant_dimensions())


if __name__ == "__main__":
    main()
