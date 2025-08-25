#!/usr/bin/env python3
"""
Script to re-ingest documents after fixing Qdrant collection dimensions.
This script will ingest documents using the correct embedding model and dimensions.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.ai.shared.tools.rag.ingest import ingest_jsonl_hybrid
from app.core.logger import logger


async def reingest_documents():
    """Re-ingest documents with the correct embedding model."""
    try:
        logger.info("🚀 Starting document re-ingestion...")
        
        # Define the paths to your JSONL files
        # Update these paths to match your actual data files
        jsonl_paths = [
            "app/services/ai/shared/tools/rag/rag_data/adn_master_company_en_2025-08-24.jsonl",
            # Add more paths as needed
        ]
        
        # Filter out non-existent files
        existing_paths = [path for path in jsonl_paths if os.path.exists(path)]
        
        if not existing_paths:
            logger.error("❌ No JSONL files found. Please update the paths in this script.")
            logger.info("💡 Expected files:")
            for path in jsonl_paths:
                logger.info(f"   - {path}")
            return
        
        logger.info(f"📁 Found {len(existing_paths)} JSONL files to ingest:")
        for path in existing_paths:
            logger.info(f"   - {path}")
        
        # Ingest documents
        logger.info("📥 Starting ingestion process...")
        vector_store = await asyncio.to_thread(
            ingest_jsonl_hybrid,
            paths=existing_paths,
            batch_size=200
        )
        
        logger.info("✅ Document re-ingestion completed successfully!")
        logger.info("🎉 Your RAG system should now work with the correct dimensions.")
        
    except Exception as e:
        logger.error(f"❌ Failed to re-ingest documents: {str(e)}")
        raise


def main():
    """Main entry point."""
    asyncio.run(reingest_documents())


if __name__ == "__main__":
    main()
