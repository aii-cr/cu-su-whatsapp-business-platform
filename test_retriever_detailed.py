#!/usr/bin/env python3
"""
Detailed test script for the hybrid retriever with comprehensive logging.
Tests various queries and provides detailed analysis of results.
"""

import asyncio
import pandas as pd
import time
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.services.ai.config import ai_config
from app.services.ai.rag.ingest import DocumentIngester
from app.services.ai.rag.retriever import get_default_retriever

class DetailedRetrieverTester:
    def __init__(self):
        self.client = QdrantClient(url=ai_config.qdrant_url, api_key=ai_config.qdrant_api_key)
        self.collection_name = 'whatsapp_business_platform'
        self.test_results = []
        
    async def setup_collection(self):
        """Set up the collection with proper indexes."""
        print("🔧 Setting up collection...")
        
        # Delete existing collection
        try:
            self.client.delete_collection(self.collection_name)
            print("✓ Collection deleted")
        except Exception as e:
            print(f"Collection deletion: {e}")
        
        # Create new collection
        self.client.create_collection(
            collection_name=self.collection_name,
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
                
                self.client.create_payload_index(self.collection_name, field_name, schema)
                print(f"✓ Created index for {field_name}")
            except Exception as e:
                print(f"- Index {field_name}: {str(e)[:50]}...")
    
    async def ingest_documents(self):
        """Ingest documents with detailed logging."""
        print("\n📥 Ingesting documents...")
        
        ingester = DocumentIngester()
        result = await ingester.ingest_csv_dataset(
            'app/services/ai/datasets/adn_rag_base_full_v1_3.csv'
        )
        
        print(f"📊 Ingestion Summary:")
        print(f"  Success: {result.success}")
        print(f"  Documents processed: {result.documents_processed}")
        print(f"  Chunks created: {result.chunks_created}")
        print(f"  Chunks stored: {result.chunks_stored}")
        print(f"  Processing time: {result.processing_time_ms}ms")
        
        if result.errors:
            print(f"  Errors: {result.errors}")
        
        return result.success
    
    async def test_query(self, query: str, expected_keywords: list = None, expected_section: str = None):
        """Test a single query with detailed analysis."""
        print(f"\n🔍 Testing Query: '{query}'")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # Get retriever
            retriever = get_default_retriever()
            
            # Execute query
            results = await retriever.aget_relevant_documents(query)
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            print(f"⏱️  Query latency: {latency_ms:.2f}ms")
            print(f"📄 Found {len(results)} documents")
            
            if not results:
                print("❌ No results found")
                return {
                    "query": query,
                    "success": False,
                    "latency_ms": latency_ms,
                    "results_count": 0,
                    "error": "No results found"
                }
            
            # Analyze results
            best_result = results[0]
            content = best_result.page_content
            metadata = best_result.metadata
            
            print(f"\n🏆 Top Result Analysis:")
            print(f"  Content length: {len(content)} characters")
            print(f"  Section: {metadata.get('section', 'N/A')}")
            print(f"  Subsection: {metadata.get('subsection', 'N/A')}")
            print(f"  Title: {metadata.get('title', 'N/A')}")
            print(f"  Tags: {metadata.get('tags', [])}")
            print(f"  Price: {metadata.get('price_text', 'N/A')}")
            print(f"  URL: {metadata.get('url', 'N/A')}")
            
            print(f"\n📝 Content Preview:")
            print(f"  {content[:300]}...")
            
            # Check for expected content
            success_indicators = []
            
            if expected_keywords:
                found_keywords = [kw for kw in expected_keywords if kw.lower() in content.lower()]
                if found_keywords:
                    success_indicators.append(f"Found expected keywords: {found_keywords}")
                else:
                    success_indicators.append(f"Missing expected keywords: {expected_keywords}")
            
            if expected_section:
                if expected_section.lower() in metadata.get('section', '').lower():
                    success_indicators.append(f"Found expected section: {expected_section}")
                else:
                    success_indicators.append(f"Expected section '{expected_section}', got '{metadata.get('section')}'")
            
            # Check for "general" content (should not be present)
            if "general" in content.lower() and len(content) < 100:
                success_indicators.append("⚠️  Content appears to be generic")
            else:
                success_indicators.append("✅ Content appears meaningful")
            
            # Overall success assessment
            success = len([s for s in success_indicators if "✅" in s or "Found" in s]) >= 2
            
            print(f"\n📊 Success Indicators:")
            for indicator in success_indicators:
                print(f"  {indicator}")
            
            print(f"\n🎯 Overall Success: {'✅ PASS' if success else '❌ FAIL'}")
            
            return {
                "query": query,
                "success": success,
                "latency_ms": latency_ms,
                "results_count": len(results),
                "content_preview": content[:200],
                "section": metadata.get('section'),
                "success_indicators": success_indicators
            }
            
        except Exception as e:
            print(f"❌ Error testing query: {e}")
            return {
                "query": query,
                "success": False,
                "latency_ms": 0,
                "results_count": 0,
                "error": str(e)
            }
    
    async def run_comprehensive_tests(self):
        """Run comprehensive tests with various query types."""
        print("🚀 Starting Comprehensive Retriever Tests")
        print("=" * 80)
        
        # Test queries with expected results
        test_cases = [
            {
                "query": "precio IPTV",
                "expected_keywords": ["iptv", "precio", "₡"],
                "expected_section": "IPTV",
                "description": "IPTV pricing information"
            },
            {
                "query": "horario administrativo",
                "expected_keywords": ["horario", "administrativo", "lunes", "viernes"],
                "expected_section": "Contacto",
                "description": "Administrative hours"
            },
            {
                "query": "telefonía precio",
                "expected_keywords": ["telefonía", "precio", "₡"],
                "expected_section": "Telefonía",
                "description": "Phone service pricing"
            },
            {
                "query": "plan 500/500",
                "expected_keywords": ["500", "plan", "residencial"],
                "expected_section": "Residencial",
                "description": "500 Mbps plan details"
            },
            {
                "query": "cobertura",
                "expected_keywords": ["cobertura", "dirección", "verificar"],
                "expected_section": "Cobertura",
                "description": "Coverage information"
            },
            {
                "query": "WhatsApp contacto",
                "expected_keywords": ["whatsapp", "contacto", "+506"],
                "expected_section": "Contacto",
                "description": "WhatsApp contact information"
            },
            {
                "query": "instalación tiempo",
                "expected_keywords": ["instalación", "horas", "tiempo"],
                "expected_section": "Residencial",
                "description": "Installation time information"
            },
            {
                "query": "métodos de pago",
                "expected_keywords": ["pago", "sinpe", "tarjeta", "transferencia"],
                "expected_section": "Pagos",
                "description": "Payment methods"
            }
        ]
        
        # Run tests
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*20} TEST {i}/{len(test_cases)} {'='*20}")
            print(f"📋 {test_case['description']}")
            
            result = await self.test_query(
                test_case["query"],
                test_case["expected_keywords"],
                test_case["expected_section"]
            )
            
            self.test_results.append(result)
            
            # Small delay between tests
            await asyncio.sleep(0.5)
        
        # Summary
        await self.print_summary()
    
    async def print_summary(self):
        """Print comprehensive test summary."""
        print(f"\n{'='*80}")
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r["success"]])
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"📈 Overall Results:")
        print(f"  Total tests: {total_tests}")
        print(f"  Successful: {successful_tests}")
        print(f"  Failed: {total_tests - successful_tests}")
        print(f"  Success rate: {success_rate:.1f}%")
        
        # Performance metrics
        latencies = [r["latency_ms"] for r in self.test_results if r["latency_ms"] > 0]
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            
            print(f"\n⏱️  Performance Metrics:")
            print(f"  Average latency: {avg_latency:.2f}ms")
            print(f"  Min latency: {min_latency:.2f}ms")
            print(f"  Max latency: {max_latency:.2f}ms")
        
        # Detailed results
        print(f"\n📋 Detailed Results:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"  {i}. {result['query']} - {status} ({result['latency_ms']:.2f}ms)")
            
            if not result["success"] and "error" in result:
                print(f"     Error: {result['error']}")
        
        # Content quality assessment
        meaningful_content = len([r for r in self.test_results if "meaningful" in str(r.get("success_indicators", []))])
        print(f"\n🎯 Content Quality:")
        print(f"  Meaningful content: {meaningful_content}/{total_tests}")
        
        # Final assessment
        if success_rate >= 80:
            print(f"\n🎉 EXCELLENT: Retriever is working well!")
        elif success_rate >= 60:
            print(f"\n✅ GOOD: Retriever is mostly working")
        else:
            print(f"\n⚠️  NEEDS IMPROVEMENT: Retriever needs fixes")

async def main():
    """Run the detailed retriever test."""
    tester = DetailedRetrieverTester()
    
    # Setup
    await tester.setup_collection()
    
    # Ingest
    success = await tester.ingest_documents()
    if not success:
        print("❌ Ingestion failed, cannot proceed with tests")
        return
    
    # Run tests
    await tester.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())
