#!/usr/bin/env python3
"""
Fix Qdrant indexes and test the retriever with detailed logging.
"""

import asyncio
import pandas as pd
import time
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.services.ai.config import ai_config
from app.services.ai.rag.ingest import DocumentIngester
from app.services.ai.rag.retriever import get_default_retriever

async def fix_qdrant_indexes():
    """Fix the Qdrant collection by recreating it with proper indexes."""
    print("🔧 Fixing Qdrant Collection...")
    
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
    
    # Create required indexes
    indexes = [
        ('tenant_id', models.PayloadFieldSchema.KEYWORD),
        ('locale', models.PayloadFieldSchema.KEYWORD),
        ('section', models.PayloadFieldSchema.KEYWORD),
        ('doc_id', models.PayloadFieldSchema.KEYWORD)
    ]
    
    for field_name, schema in indexes:
        try:
            client.create_payload_index(collection_name, field_name, schema)
            print(f"✓ Created index for {field_name}")
        except Exception as e:
            print(f"❌ Failed to create index for {field_name}: {e}")

async def ingest_documents():
    """Ingest documents with the fixed collection."""
    print("\n📥 Ingesting documents...")
    
    ingester = DocumentIngester()
    result = await ingester.ingest_csv_dataset(
        'app/services/ai/datasets/adn_rag_base_full_v1_3.csv'
    )
    
    print(f"📊 Ingestion Result:")
    print(f"  Success: {result.success}")
    print(f"  Documents processed: {result.documents_processed}")
    print(f"  Chunks stored: {result.chunks_stored}")
    print(f"  Processing time: {result.processing_time_ms}ms")
    
    return result.success

async def test_query_detailed(query: str, expected_keywords: list = None):
    """Test a single query with detailed analysis."""
    print(f"\n🔍 Testing: '{query}'")
    print("-" * 50)
    
    start_time = time.time()
    
    try:
        retriever = get_default_retriever()
        results = await retriever.aget_relevant_documents(query)
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        print(f"⏱️  Latency: {latency_ms:.2f}ms")
        print(f"📄 Results found: {len(results)}")
        
        if not results:
            print("❌ No results found")
            return False
        
        # Analyze top result
        best_result = results[0]
        content = best_result.page_content
        metadata = best_result.metadata
        
        print(f"\n🏆 Top Result:")
        print(f"  Section: {metadata.get('section', 'N/A')}")
        print(f"  Title: {metadata.get('title', 'N/A')}")
        print(f"  Content length: {len(content)} chars")
        
        print(f"\n📝 Content Preview:")
        print(f"  {content[:300]}...")
        
        # Check for expected keywords
        if expected_keywords:
            found_keywords = [kw for kw in expected_keywords if kw.lower() in content.lower()]
            if found_keywords:
                print(f"✅ Found keywords: {found_keywords}")
            else:
                print(f"❌ Missing keywords: {expected_keywords}")
        
        # Check for generic content
        if "general" in content.lower() and len(content) < 100:
            print("❌ Content is still generic!")
            return False
        else:
            print("✅ Content is meaningful!")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def run_comprehensive_tests():
    """Run comprehensive tests with various queries."""
    print("\n🚀 Running Comprehensive Tests")
    print("=" * 60)
    
    test_cases = [
        {
            "query": "precio IPTV",
            "keywords": ["iptv", "precio", "₡"],
            "description": "IPTV pricing"
        },
        {
            "query": "horario administrativo",
            "keywords": ["horario", "administrativo", "lunes", "viernes"],
            "description": "Admin hours"
        },
        {
            "query": "telefonía precio",
            "keywords": ["telefonía", "precio", "₡"],
            "description": "Phone pricing"
        },
        {
            "query": "plan 500/500",
            "keywords": ["500", "plan", "residencial"],
            "description": "500 Mbps plan"
        },
        {
            "query": "cobertura",
            "keywords": ["cobertura", "dirección", "verificar"],
            "description": "Coverage info"
        },
        {
            "query": "WhatsApp contacto",
            "keywords": ["whatsapp", "contacto", "+506"],
            "description": "WhatsApp contact"
        },
        {
            "query": "instalación tiempo",
            "keywords": ["instalación", "horas", "tiempo"],
            "description": "Installation time"
        },
        {
            "query": "métodos de pago",
            "keywords": ["pago", "sinpe", "tarjeta"],
            "description": "Payment methods"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*20} TEST {i}/{len(test_cases)} {'='*20}")
        print(f"📋 {test_case['description']}")
        
        success = await test_query_detailed(
            test_case["query"], 
            test_case["keywords"]
        )
        
        results.append({
            "query": test_case["query"],
            "description": test_case["description"],
            "success": success
        })
        
        # Small delay between tests
        await asyncio.sleep(0.5)
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    successful_tests = len([r for r in results if r["success"]])
    success_rate = (successful_tests / total_tests) * 100
    
    print(f"Total tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Success rate: {success_rate:.1f}%")
    
    print(f"\nDetailed Results:")
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"  {i}. {result['query']} - {status}")
    
    if success_rate >= 80:
        print(f"\n🎉 EXCELLENT! Retriever is working perfectly!")
    elif success_rate >= 60:
        print(f"\n✅ GOOD! Retriever is mostly working")
    else:
        print(f"\n⚠️  NEEDS IMPROVEMENT: Retriever needs fixes")

async def main():
    """Main test function."""
    print("🚀 Fix and Test Retriever")
    print("=" * 50)
    
    # Step 1: Fix Qdrant indexes
    await fix_qdrant_indexes()
    
    # Step 2: Ingest documents
    success = await ingest_documents()
    if not success:
        print("❌ Ingestion failed, cannot proceed")
        return
    
    # Step 3: Run tests
    await run_comprehensive_tests()
    
    print(f"\n🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
