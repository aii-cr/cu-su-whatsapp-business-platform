#!/usr/bin/env python3
"""
Basic RAG Testing
Simple tests for RAG functionality without complex evaluation.
"""

import asyncio
import time
import json
from typing import List, Dict, Any
from datetime import datetime

# LangChain imports
from langchain_core.documents import Document

# Qdrant imports
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Local imports
from app.services.ai.config import ai_config
from app.services.ai.rag.ingest import DocumentIngester
from app.services.ai.rag.retriever import get_default_retriever

class BasicRAGTester:
    """Basic RAG testing with simple evaluation metrics."""
    
    def __init__(self):
        self.client = QdrantClient(url=ai_config.qdrant_url, api_key=ai_config.qdrant_api_key)
        self.collection_name = 'whatsapp_business_platform'
        self.test_results = []
        
    async def setup_collection(self):
        """Set up the collection with proper indexes."""
        print("🔧 Setting up Qdrant collection...")
        
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
        
        # Create indexes for better performance
        indexes = [
            ('tenant_id', 'keyword'),
            ('locale', 'keyword'),
            ('section', 'keyword'),
            ('subsection', 'keyword'),
            ('doc_id', 'keyword'),
            ('tags', 'keyword'),
            ('is_faq', 'keyword'),
            ('is_promo', 'keyword')
        ]
        
        for field_name, field_type in indexes:
            try:
                schema = models.PayloadFieldSchema.KEYWORD
                self.client.create_payload_index(self.collection_name, field_name, schema)
                print(f"✓ Created index for {field_name}")
            except Exception as e:
                print(f"⚠️  Index {field_name}: {str(e)[:50]}...")
    
    async def ingest_documents(self):
        """Ingest documents with detailed logging."""
        print("\n📥 Ingesting ADN dataset...")
        
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
    
    def create_test_queries(self) -> List[Dict[str, Any]]:
        """Create basic test queries for core functionality."""
        return [
            # Core functionality tests
            {
                "query": "¿Cuál es el precio del plan de 500 Mbps?",
                "expected_section": "Residencial",
                "expected_keywords": ["500", "₡33 410", "plan"],
                "category": "pricing",
                "difficulty": "easy"
            },
            {
                "query": "¿Cuántos canales tiene el IPTV?",
                "expected_section": "IPTV",
                "expected_keywords": ["88 canales", "lista"],
                "category": "service_info",
                "difficulty": "easy"
            },
            {
                "query": "¿Cuál es el número de WhatsApp?",
                "expected_section": "Contacto",
                "expected_keywords": ["+506 7087-8240", "WhatsApp"],
                "category": "contact",
                "difficulty": "easy"
            },
            {
                "query": "¿Quién es ADN?",
                "expected_section": "Compañía",
                "expected_keywords": ["American Data Networks", "2005", "telecomunicaciones"],
                "category": "company",
                "difficulty": "easy"
            },
            {
                "query": "¿Cuánto tiempo toma la instalación?",
                "expected_section": "Residencial",
                "expected_keywords": ["48", "72", "horas"],
                "category": "installation",
                "difficulty": "medium"
            }
        ]
    
    async def test_retriever_performance(self, query: str, expected_info: Dict[str, Any]) -> Dict[str, Any]:
        """Test retriever performance for a single query."""
        print(f"\n🔍 Testing: '{query}'")
        
        start_time = time.time()
        
        try:
            # Get retriever
            retriever = get_default_retriever(tenant_id=None, locale=None)
            
            # Execute query
            results = await retriever.aget_relevant_documents(query)
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            # Analyze results
            analysis = self._analyze_results(results, expected_info)
            
            # Generate answer from context
            context = "\n".join([doc.page_content for doc in results[:3]]) if results else ""
            generated_answer = self._generate_answer_from_context(context, query)
            
            return {
                "query": query,
                "latency_ms": latency_ms,
                "results_count": len(results),
                "analysis": analysis,
                "generated_answer": generated_answer,
                "context_preview": context[:200] + "..." if len(context) > 200 else context,
                "success": analysis["relevance_score"] > 0.6
            }
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                "query": query,
                "latency_ms": 0,
                "results_count": 0,
                "error": str(e),
                "success": False
            }
    
    def _analyze_results(self, results: List[Document], expected_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze retrieval results for relevance and accuracy."""
        if not results:
            return {
                "relevance_score": 0.0,
                "section_match": False,
                "keyword_matches": [],
                "content_quality": "none"
            }
        
        # Get expected information
        expected_section = expected_info.get("expected_section", "").lower()
        expected_keywords = [kw.lower() for kw in expected_info.get("expected_keywords", [])]
        
        # Analyze top result
        top_result = results[0]
        content = top_result.page_content.lower()
        metadata = top_result.metadata
        
        # Check section match
        section_match = expected_section in metadata.get("section", "").lower()
        
        # Check keyword matches
        keyword_matches = [kw for kw in expected_keywords if kw in content]
        keyword_score = len(keyword_matches) / len(expected_keywords) if expected_keywords else 0
        
        # Assess content quality
        content_length = len(top_result.page_content)
        if content_length > 200:
            content_quality = "excellent"
        elif content_length > 100:
            content_quality = "good"
        elif content_length > 50:
            content_quality = "fair"
        else:
            content_quality = "poor"
        
        # Calculate overall relevance score
        relevance_score = (
            (0.4 * keyword_score) +
            (0.3 * (1.0 if section_match else 0.0)) +
            (0.3 * min(content_length / 200, 1.0))
        )
        
        return {
            "relevance_score": relevance_score,
            "section_match": section_match,
            "keyword_matches": keyword_matches,
            "keyword_score": keyword_score,
            "content_quality": content_quality,
            "content_length": content_length,
            "section": metadata.get("section"),
            "title": metadata.get("title")
        }
    
    def _generate_answer_from_context(self, context: str, question: str) -> str:
        """Generate a simple answer from context."""
        if not context:
            return "No se encontró información relevante."
        
        # Simple answer generation based on question type
        question_lower = question.lower()
        
        if "precio" in question_lower or "costo" in question_lower or "cuánto" in question_lower:
            # Look for price information
            if "₡" in context:
                price_match = context.split("₡")[1].split()[0] if "₡" in context else "no especificado"
                return f"El precio es {price_match} colones."
        
        if "canales" in question_lower:
            if "88" in context:
                return "El servicio IPTV incluye 88 canales."
        
        if "whatsapp" in question_lower:
            if "+506 7087-8240" in context:
                return "El número de WhatsApp es +506 7087-8240."
        
        if "instalación" in question_lower or "tiempo" in question_lower:
            if "48" in context and "72" in context:
                return "La instalación se realiza entre 48 y 72 horas posteriores a la compra."
        
        # Default: return first sentence of context
        sentences = context.split('.')
        return sentences[0] + "." if sentences else context[:100] + "..."
    
    async def run_basic_tests(self):
        """Run basic RAG tests."""
        print("🚀 Starting Basic RAG Testing")
        print("=" * 80)
        
        # Get test queries
        test_queries = self.create_test_queries()
        
        print(f"📋 Testing {len(test_queries)} queries for core functionality...")
        
        # Run tests
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n{'='*20} TEST {i}/{len(test_queries)} {'='*20}")
            print(f"📋 Category: {test_case['category']} | Difficulty: {test_case['difficulty']}")
            
            result = await self.test_retriever_performance(
                test_case["query"],
                test_case
            )
            
            self.test_results.append(result)
            
            # Print result summary
            if result["success"]:
                print(f"✅ PASS - Latency: {result['latency_ms']:.2f}ms, Relevance: {result['analysis']['relevance_score']:.3f}")
                print(f"📝 Answer: {result['generated_answer']}")
            else:
                print(f"❌ FAIL - Latency: {result['latency_ms']:.2f}ms, Relevance: {result['analysis']['relevance_score']:.3f}")
                if "error" in result:
                    print(f"💥 Error: {result['error']}")
            
            # Small delay between tests
            await asyncio.sleep(0.5)
        
        # Print summary
        await self.print_summary()
    
    async def print_summary(self):
        """Print test summary."""
        print(f"\n{'='*80}")
        print("📊 BASIC RAG TEST SUMMARY")
        print("=" * 80)
        
        # Basic metrics
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r["success"]])
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"📈 Basic Performance:")
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
        
        # Quality assessment
        relevance_scores = [r["analysis"]["relevance_score"] for r in self.test_results if "analysis" in r]
        if relevance_scores:
            avg_relevance = sum(relevance_scores) / len(relevance_scores)
            print(f"\n🎯 Content Quality Analysis:")
            print(f"  Average relevance score: {avg_relevance:.3f}")
            print(f"  High relevance (>0.8): {len([s for s in relevance_scores if s > 0.8])}")
            print(f"  Medium relevance (0.5-0.8): {len([s for s in relevance_scores if 0.5 <= s <= 0.8])}")
            print(f"  Low relevance (<0.5): {len([s for s in relevance_scores if s < 0.5])}")
        
        # Final assessment
        if success_rate >= 80:
            print(f"\n🎉 EXCELLENT: RAG system is working well!")
        elif success_rate >= 60:
            print(f"\n✅ GOOD: RAG system is mostly working")
        else:
            print(f"\n⚠️  NEEDS IMPROVEMENT: RAG system needs fixes")
        
        # Save results
        self._save_test_results()
    
    def _save_test_results(self):
        """Save test results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tests/ai/rag_basic_test_results_{timestamp}.json"
        
        results_data = {
            "timestamp": timestamp,
            "test_results": self.test_results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Results saved to: {filename}")

async def main():
    """Run the basic RAG test."""
    tester = BasicRAGTester()
    
    # Setup
    await tester.setup_collection()
    
    # Ingest
    success = await tester.ingest_documents()
    if not success:
        print("❌ Ingestion failed, cannot proceed with tests")
        return
    
    # Run basic tests
    await tester.run_basic_tests()

if __name__ == "__main__":
    asyncio.run(main())
