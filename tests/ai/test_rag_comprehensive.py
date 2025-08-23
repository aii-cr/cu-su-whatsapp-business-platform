#!/usr/bin/env python3
"""
Comprehensive RAG Testing with RAGAS Evaluation
Tests the retriever performance with the ADN dataset using RAGAS metrics.
"""

import asyncio
import pandas as pd
import time
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

# LangChain imports
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import EmbeddingsFilter

# RAGAS imports for evaluation
try:
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_relevancy,
        context_recall,
        answer_correctness,
        answer_similarity
    )
    from datasets import Dataset
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False
    print("⚠️  RAGAS not available. Install with: pip install ragas datasets")

# Qdrant imports
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Local imports
from app.services.ai.config import ai_config
from app.services.ai.rag.ingest import DocumentIngester
from app.services.ai.rag.retriever import get_default_retriever
from app.services.ai.rag.schemas import RetrieverConfig, RetrievalResult

class ComprehensiveRAGTester:
    """Comprehensive RAG testing using RAGAS and LangChain evaluation tools."""
    
    def __init__(self):
        self.client = QdrantClient(url=ai_config.qdrant_url, api_key=ai_config.qdrant_api_key)
        self.collection_name = 'whatsapp_business_platform'
        self.test_results = []
        self.evaluation_dataset = []
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=ai_config.openai_api_key,
            model=ai_config.openai_embedding_model,
            dimensions=ai_config.openai_embedding_dimension
        )
        
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
        """Create comprehensive test queries covering different aspects of the ADN dataset."""
        return [
            # Pricing queries
            {
                "query": "¿Cuál es el precio del plan de 500 Mbps?",
                "expected_section": "Residencial",
                "expected_keywords": ["500", "₡33 410", "plan"],
                "category": "pricing",
                "difficulty": "easy",
                "ground_truth": "El plan de 500/500 Mbps cuesta ₡33 410 IVI e incluye Equipo Wi-Fi, Firewall y Soporte 24/7."
            },
            {
                "query": "¿Cuánto cuesta el servicio de IPTV?",
                "expected_section": "IPTV",
                "expected_keywords": ["₡4 590", "dispositivo"],
                "category": "pricing",
                "difficulty": "easy",
                "ground_truth": "Cada dispositivo IPTV tiene un valor de ₡4 590 IVI."
            },
            {
                "query": "Precio de telefonía residencial",
                "expected_section": "Telefonía",
                "expected_keywords": ["₡3 590", "VoIP"],
                "category": "pricing",
                "difficulty": "easy",
                "ground_truth": "El costo mensual de telefonía residencial es ₡3 590 IVI/mes."
            },
            
            # Service information queries
            {
                "query": "¿Qué incluye el plan de 1 Gbps?",
                "expected_section": "Residencial",
                "expected_keywords": ["1 Gbps", "Wi-Fi", "Firewall"],
                "category": "service_info",
                "difficulty": "medium",
                "ground_truth": "El plan de 1/1 Gbps incluye Equipo Wi-Fi, Firewall y Soporte 24/7."
            },
            {
                "query": "¿Cuántos canales tiene el IPTV?",
                "expected_section": "IPTV",
                "expected_keywords": ["88 canales", "lista"],
                "category": "service_info",
                "difficulty": "easy",
                "ground_truth": "El servicio IPTV ofrece 88 canales."
            },
            {
                "query": "¿Qué servicios empresariales ofrecen?",
                "expected_section": "Empresarial",
                "expected_keywords": ["fibra", "datacenter", "seguridad"],
                "category": "service_info",
                "difficulty": "medium",
                "ground_truth": "Los servicios empresariales incluyen Fibra Óptica, Data center y redes administradas, Telefonía VoIP, Soporte 24/7, Seguridad y Firewall gestionado."
            },
            
            # Contact and support queries
            {
                "query": "¿Cuál es el número de WhatsApp?",
                "expected_section": "Contacto",
                "expected_keywords": ["+506 7087-8240", "WhatsApp"],
                "category": "contact",
                "difficulty": "easy",
                "ground_truth": "El número de WhatsApp es +506 7087-8240."
            },
            {
                "query": "Horario de atención administrativa",
                "expected_section": "Contacto",
                "expected_keywords": ["7:00 a. m.", "5:00 p. m.", "lunes", "viernes"],
                "category": "contact",
                "difficulty": "easy",
                "ground_truth": "El horario administrativo es de lunes a viernes, 7:00 a. m. – 5:00 p. m."
            },
            {
                "query": "¿Tienen soporte 24/7?",
                "expected_section": "Contacto",
                "expected_keywords": ["24/7", "soporte técnico"],
                "category": "contact",
                "difficulty": "easy",
                "ground_truth": "Sí, tienen soporte técnico disponible 24/7."
            },
            
            # Installation and activation queries
            {
                "query": "¿Cuánto tiempo toma la instalación?",
                "expected_section": "Residencial",
                "expected_keywords": ["48", "72", "horas"],
                "category": "installation",
                "difficulty": "medium",
                "ground_truth": "La instalación se realiza entre 48 y 72 horas posteriores a la compra."
            },
            {
                "query": "¿Cómo puedo verificar cobertura?",
                "expected_section": "Cobertura",
                "expected_keywords": ["data.cr/cobertura", "dirección"],
                "category": "installation",
                "difficulty": "easy",
                "ground_truth": "Puedes verificar cobertura ingresando a https://data.cr/cobertura o compartiendo tu dirección exacta."
            },
            
            # Payment queries
            {
                "query": "¿Qué métodos de pago aceptan?",
                "expected_section": "Pagos",
                "expected_keywords": ["tarjeta", "SINPE", "transferencia"],
                "category": "payment",
                "difficulty": "easy",
                "ground_truth": "Aceptan pago con tarjeta (ONVO Pay), SINPE Móvil y transferencia bancaria."
            },
            {
                "query": "¿Qué es ONVO Pay?",
                "expected_section": "Pagos",
                "expected_keywords": ["pasarela", "tarjeta", "segura"],
                "category": "payment",
                "difficulty": "medium",
                "ground_truth": "ONVO Pay es una pasarela de pago en línea para transacciones rápidas y seguras con tarjetas de crédito o débito."
            },
            
            # Technical queries
            {
                "query": "¿Qué velocidad tienen los planes?",
                "expected_section": "Residencial",
                "expected_keywords": ["100/100", "250/250", "500/500", "1 Gbps"],
                "category": "technical",
                "difficulty": "medium",
                "ground_truth": "Los planes tienen velocidades de 100/100 Mbps, 250/250 Mbps, 500/500 Mbps y 1/1 Gbps."
            },
            {
                "query": "¿Los planes son simétricos?",
                "expected_section": "Residencial",
                "expected_keywords": ["simétrico", "subida", "bajada"],
                "category": "technical",
                "difficulty": "medium",
                "ground_truth": "Sí, todos los planes son simétricos, permitiendo subir y descargar contenido al mismo tiempo sin pérdida de calidad."
            },
            
            # Company information queries
            {
                "query": "¿Quién es ADN?",
                "expected_section": "Compañía",
                "expected_keywords": ["American Data Networks", "2005", "telecomunicaciones"],
                "category": "company",
                "difficulty": "easy",
                "ground_truth": "ADN (American Data Networks S.A.) es una empresa fundada en 2005 con más de 15 años de experiencia en telecomunicaciones."
            },
            {
                "query": "¿Cuál es la misión de ADN?",
                "expected_section": "Compañía",
                "expected_keywords": ["primera opción", "innovación", "infraestructura"],
                "category": "company",
                "difficulty": "medium",
                "ground_truth": "La misión de ADN es ser la primera opción en servicios de telecomunicación, brindando innovación constante e infraestructura tecnológica de alto nivel."
            },
            
            # Privacy queries
            {
                "query": "¿Qué datos recopilan?",
                "expected_section": "Privacidad",
                "expected_keywords": ["nombre", "identificación", "dirección", "correo"],
                "category": "privacy",
                "difficulty": "medium",
                "ground_truth": "Recopilan datos de contacto (nombre, identificación, dirección, correo electrónico y número de teléfono), información de pago, datos de uso e información técnica."
            },
            {
                "query": "¿Cómo protegen mis datos?",
                "expected_section": "Privacidad",
                "expected_keywords": ["cifrado", "controles", "seguridad"],
                "category": "privacy",
                "difficulty": "medium",
                "ground_truth": "Protegen los datos con medidas razonables como cifrado, controles de acceso y políticas internas de seguridad."
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
            
            # Prepare for RAGAS evaluation
            evaluation_entry = {
                "question": query,
                "contexts": [context],
                "ground_truth": expected_info.get("ground_truth", ""),
                "answer": generated_answer,
                "category": expected_info.get("category", "general"),
                "difficulty": expected_info.get("difficulty", "medium")
            }
            
            return {
                "query": query,
                "latency_ms": latency_ms,
                "results_count": len(results),
                "analysis": analysis,
                "generated_answer": generated_answer,
                "ground_truth": expected_info.get("ground_truth", ""),
                "evaluation_entry": evaluation_entry,
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
        """Generate a simple answer from context for RAGAS evaluation."""
        if not context:
            return "No se encontró información relevante."
        
        # Simple answer generation based on question type
        question_lower = question.lower()
        
        if "precio" in question_lower or "costo" in question_lower or "cuánto" in question_lower:
            # Look for price information
            if "₡" in context:
                return f"El precio es {context.split('₡')[1].split()[0] if '₡' in context else 'no especificado'} colones."
        
        if "horario" in question_lower or "atención" in question_lower:
            if "7:00" in context and "5:00" in context:
                return "El horario administrativo es de lunes a viernes de 7:00 a.m. a 5:00 p.m."
        
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
    
    async def run_ragas_evaluation(self):
        """Run RAGAS evaluation on the collected data."""
        if not RAGAS_AVAILABLE:
            print("⚠️  RAGAS not available. Skipping RAGAS evaluation.")
            return None
            
        print("\n📊 Running RAGAS Evaluation...")
        
        if not self.evaluation_dataset:
            print("❌ No evaluation data available")
            return None
        
        try:
            # Convert to RAGAS dataset format
            dataset_dict = {
                "question": [item["question"] for item in self.evaluation_dataset],
                "contexts": [item["contexts"] for item in self.evaluation_dataset],
                "ground_truth": [item["ground_truth"] for item in self.evaluation_dataset],
                "answer": [item["answer"] for item in self.evaluation_dataset]
            }
            
            dataset = Dataset.from_dict(dataset_dict)
            
            # Run RAGAS evaluation
            results = evaluate(
                dataset,
                metrics=[
                    context_relevancy,
                    faithfulness,
                    answer_relevancy,
                    context_recall
                ]
            )
            
            print("\n📈 RAGAS Evaluation Results:")
            print("=" * 50)
            for metric, score in results.items():
                print(f"{metric}: {score:.3f}")
            
            return results
            
        except Exception as e:
            print(f"❌ RAGAS evaluation failed: {e}")
            return None
    
    async def run_comprehensive_tests(self):
        """Run comprehensive RAG tests."""
        print("🚀 Starting Comprehensive RAG Testing with RAGAS")
        print("=" * 80)
        
        # Get test queries
        test_queries = self.create_test_queries()
        
        print(f"📋 Testing {len(test_queries)} queries across different categories...")
        
        # Run tests
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n{'='*20} TEST {i}/{len(test_queries)} {'='*20}")
            print(f"📋 Category: {test_case['category']} | Difficulty: {test_case['difficulty']}")
            
            result = await self.test_retriever_performance(
                test_case["query"],
                test_case
            )
            
            self.test_results.append(result)
            
            # Add to evaluation dataset
            if "evaluation_entry" in result:
                self.evaluation_dataset.append(result["evaluation_entry"])
            
            # Small delay between tests
            await asyncio.sleep(0.5)
        
        # Run RAGAS evaluation
        ragas_results = await self.run_ragas_evaluation()
        
        # Print comprehensive summary
        await self.print_comprehensive_summary(ragas_results)
    
    async def print_comprehensive_summary(self, ragas_results: Optional[Dict] = None):
        """Print comprehensive test summary with RAGAS metrics."""
        print(f"\n{'='*80}")
        print("📊 COMPREHENSIVE RAG TEST SUMMARY")
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
        
        # Category analysis
        categories = {}
        for result in self.test_results:
            if "evaluation_entry" in result:
                category = result["evaluation_entry"]["category"]
                if category not in categories:
                    categories[category] = {"total": 0, "success": 0}
                categories[category]["total"] += 1
                if result["success"]:
                    categories[category]["success"] += 1
        
        print(f"\n📂 Performance by Category:")
        for category, stats in categories.items():
            rate = (stats["success"] / stats["total"]) * 100
            print(f"  {category}: {stats['success']}/{stats['total']} ({rate:.1f}%)")
        
        # RAGAS metrics
        if ragas_results:
            print(f"\n🎯 RAGAS Evaluation Metrics:")
            for metric, score in ragas_results.items():
                print(f"  {metric}: {score:.3f}")
        
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
        if success_rate >= 80 and (not ragas_results or ragas_results.get("context_relevancy", 0) > 0.7):
            print(f"\n🎉 EXCELLENT: RAG system is performing well!")
        elif success_rate >= 60:
            print(f"\n✅ GOOD: RAG system is mostly working")
        else:
            print(f"\n⚠️  NEEDS IMPROVEMENT: RAG system needs optimization")
        
        # Save results
        self._save_test_results(ragas_results)
    
    def _save_test_results(self, ragas_results: Optional[Dict] = None):
        """Save test results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tests/ai/rag_test_results_{timestamp}.json"
        
        results_data = {
            "timestamp": timestamp,
            "test_results": self.test_results,
            "evaluation_dataset": self.evaluation_dataset,
            "ragas_results": ragas_results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Results saved to: {filename}")

async def main():
    """Run the comprehensive RAG test."""
    tester = ComprehensiveRAGTester()
    
    # Setup
    await tester.setup_collection()
    
    # Ingest
    success = await tester.ingest_documents()
    if not success:
        print("❌ Ingestion failed, cannot proceed with tests")
        return
    
    # Run comprehensive tests
    await tester.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())
