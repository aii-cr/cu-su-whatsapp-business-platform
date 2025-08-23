#!/usr/bin/env python3
"""
Test script to verify CSV content extraction is working correctly.
"""

import pandas as pd
import asyncio
from app.services.ai.rag.ingest import DocumentIngester

async def test_content_extraction():
    """Test the content extraction from CSV rows."""
    
    # Load CSV data
    df = pd.read_csv('app/services/ai/datasets/adn_rag_base_full_v1_3.csv')
    print(f"Loaded {len(df)} rows from CSV")
    
    # Create ingester
    ingester = DocumentIngester()
    
    # Test first few rows
    for idx, row in df.head(5).iterrows():
        print(f"\n=== ROW {idx} ===")
        print(f"Original row data:")
        print(f"  id: {row.get('id', 'N/A')}")
        print(f"  section: {row.get('section', 'N/A')}")
        print(f"  title: {row.get('title', 'N/A')}")
        print(f"  details: {row.get('details', 'N/A')[:100]}...")
        
        # Test content extraction
        content = ingester._build_canonical_content_from_row(row)
        print(f"\nExtracted content:")
        print(f"  {content[:200]}...")
        
        # Test metadata extraction
        metadata = ingester._extract_enhanced_metadata_from_row(row)
        print(f"\nExtracted metadata:")
        print(f"  title: {metadata.get('title')}")
        print(f"  section: {metadata.get('section')}")
        print(f"  tags: {metadata.get('tags')}")
        print(f"  price_text: {metadata.get('price_text')}")
        print(f"  is_faq: {metadata.get('is_faq')}")
        print(f"  is_promo: {metadata.get('is_promo')}")
        
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_content_extraction())
