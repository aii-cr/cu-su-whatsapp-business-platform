#!/usr/bin/env python3
"""
Complete test script for the hybrid retriever with proper CSV ingestion.
"""

import asyncio
import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.services.ai.config import ai_config
from app.services.ai.rag.ingest import DocumentIngester
from app.services.ai.rag.retriever import get_default_retriever

async def recreate_collection():
    """Delete and recreate the collection with proper indexes."""
    client = QdrantClient(url=ai_config.qdrant_url, api_key=ai_config.qdrant_api_key)
    collection_name = 'whatsapp_business_platform'
    
    # Delete existing collection
    try:
        client.delete_collection(collection_name)
        print("✓ Collection deleted")
    except Exception as e:
        print(f"Collection deletion: {e}")
    
    # Create new collection
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=1536,
            distance=models.Distance.COSINE
        )
    )
    print("✓ Collection created")
    
    # Create indexes
    indexes = [
        ('tenant_id', 'keyword'),
        ('locale', 'keyword'),
        ('section', 'keyword'),
        ('doc_id', 'keyword')
    ]
    
    for field_name, field_type in indexes:
        try:
            if field_type == "keyword":
                schema = models.PayloadFieldSchema.KEYWORD
            else:
                schema = models.PayloadFieldSchema.KEYWORD
            
            client.create_payload_index(collection_name, field_name, schema)
            print(f"✓ Created index for {field_name}")
        except Exception as e:
            print(f"- Index {field_name}: {str(e)[:50]}...")

async def test_content_extraction():
    """Test content extraction from CSV."""
    df = pd.read_csv('app/services/ai/datasets/adn_rag_base_full_v1_3.csv')
    ingester = DocumentIngester()
    
    print("\n=== CONTENT EXTRACTION TEST ===")
    
    # Test a few specific rows
    test_rows = [
        (0, "Company description"),
        (16, "Plan 500/500 Mbps"),
        (32, "IPTV price"),
        (33, "Telefonía price"),
        (11, "Horario administrativo")
    ]
    
    for row_idx, description in test_rows:
        if row_idx < len(df):
            row = df.iloc[row_idx]
            content = ingester._build_canonical_content_from_row(row)
            print(f"\n{description} (Row {row_idx}):")
            print(f"Content: {content[:150]}...")
            
            if "general" in content.lower():
                print("⚠️  WARNING: Content still contains 'general'")
            else:
                print("✅ Content looks good")

async def ingest_and_test():
    """Ingest documents and test retrieval."""
    print("\n=== INGESTION AND TESTING ===")
    
    # Ingest documents
    ingester = DocumentIngester()
    result = await ingester.ingest_csv_dataset(
        'app/services/ai/datasets/adn_rag_base_full_v1_3.csv'
    )
    
    print(f"Ingestion result: {result.model_dump()}")
    
    if not result.success:
        print("❌ Ingestion failed")
        return
    
    # Test retrieval
    retriever = get_default_retriever()
    
    test_queries = [
        "precio IPTV",
        "horario administrativo", 
        "telefonía precio",
        "plan 500/500",
        "cobertura"
    ]
    
    print("\n=== RETRIEVAL TESTS ===")
    
    for query in test_queries:
        try:
            results = await retriever.aget_relevant_documents(query)
            print(f"\nQuery: '{query}'")
            print(f"Found {len(results)} documents")
            
            if results:
                # Show first result
                first_doc = results[0]
                content = first_doc.page_content[:200] + "..." if len(first_doc.page_content) > 200 else first_doc.page_content
                print(f"Top result: {content}")
                
                # Check if content is meaningful
                if "general" in first_doc.page_content.lower():
                    print("⚠️  WARNING: Result still contains 'general'")
                else:
                    print("✅ Result looks good")
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ Error testing query '{query}': {e}")

async def main():
    """Run complete test suite."""
    print("🚀 Starting Complete Retriever Test")
    
    # Step 1: Recreate collection
    await recreate_collection()
    
    # Step 2: Test content extraction
    await test_content_extraction()
    
    # Step 3: Ingest and test
    await ingest_and_test()
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    asyncio.run(main())
