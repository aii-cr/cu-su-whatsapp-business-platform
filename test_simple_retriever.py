#!/usr/bin/env python3
"""
Simple test script to verify the retriever is working correctly.
"""

import asyncio
import pandas as pd
from app.services.ai.rag.ingest import DocumentIngester
from app.services.ai.rag.retriever import get_default_retriever

async def test_content_extraction():
    """Test that content is being extracted correctly from CSV."""
    print("🔍 Testing Content Extraction...")
    
    df = pd.read_csv('app/services/ai/datasets/adn_rag_base_full_v1_3.csv')
    ingester = DocumentIngester()
    
    # Test a few specific rows
    test_cases = [
        (0, "Company description"),
        (16, "Plan 500/500 Mbps"),
        (32, "IPTV price"),
        (11, "Horario administrativo")
    ]
    
    for row_idx, description in test_cases:
        if row_idx < len(df):
            row = df.iloc[row_idx]
            content = ingester._build_canonical_content_from_row(row)
            
            print(f"\n{description} (Row {row_idx}):")
            print(f"Content: {content[:150]}...")
            
            if "general" in content.lower() and len(content) < 100:
                print("❌ Content is still generic!")
            else:
                print("✅ Content looks good!")

async def test_retriever():
    """Test the retriever with basic queries."""
    print("\n🔍 Testing Retriever...")
    
    retriever = get_default_retriever()
    
    test_queries = [
        "precio IPTV",
        "horario administrativo",
        "telefonía precio",
        "plan 500/500"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        try:
            results = await retriever.aget_relevant_documents(query)
            print(f"Found {len(results)} documents")
            
            if results:
                content = results[0].page_content
                print(f"Top result: {content[:200]}...")
                
                if "general" in content.lower() and len(content) < 100:
                    print("❌ Result is still generic!")
                else:
                    print("✅ Result looks good!")
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ Error: {e}")

async def main():
    """Run simple tests."""
    print("🚀 Simple Retriever Test")
    print("=" * 50)
    
    # Test content extraction
    await test_content_extraction()
    
    # Test retriever
    await test_retriever()
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    asyncio.run(main())
