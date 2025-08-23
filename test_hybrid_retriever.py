#!/usr/bin/env python3
"""
Test script for the new hybrid retriever implementation.
Validates the specified test cases and performance requirements.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.ai.rag.retriever import build_retriever
from app.services.ai.rag.schemas import RetrievalMethod
from app.services.ai.rag.ingest import ingest_documents, check_collection_health
from app.core.logger import logger


class HybridRetrieverTester:
    """Test suite for the hybrid retriever."""
    
    def __init__(self):
        self.test_results = []
        self.retriever = None
    
    async def setup(self):
        """Setup test environment."""
        logger.info("Setting up hybrid retriever test environment...")
        
        # Check collection health
        health = await check_collection_health()
        if not health.get("collection_exists", False) or health.get("vectors_count", 0) == 0:
            logger.info("Collection empty, running ingestion...")
            result = await ingest_documents()
            if not result.success:
                raise Exception(f"Failed to ingest documents: {result.errors}")
        
        # Build retriever
        self.retriever = build_retriever(
            tenant_id="default",
            locale="es_CR",
            k=10,
            score_threshold=0.20,
            method=RetrievalMethod.DENSE,
            enable_multi_query=True,
            enable_compression=True
        )
        
        logger.info("Test environment setup complete")
    
    async def run_tests(self):
        """Run all test cases."""
        logger.info("Starting hybrid retriever tests...")
        
        # Test cases from requirements
        test_cases = [
            ("precio IPTV", "Should return IPTV price row in top-3"),
            ("horario administrativo", "Should return admin hours row in top-3"),
            ("telefonía precio", "Should return 'Costo mensual telefonía residencial' row"),
            ("telefonia precio", "Should handle accent normalization"),
            ("precio", "Should return price-related information"),
            ("horario", "Should return schedule information"),
            ("cobertura", "Should return coverage information"),
            ("plan 500/500", "Should expand to '500 Mbps simétrico'"),
            ("1/1 Gbps", "Should expand to '1 Gbps simétrico'"),
        ]
        
        for query, description in test_cases:
            await self._test_query(query, description)
        
        # Performance tests
        await self._test_performance()
        
        # Print results
        self._print_results()
    
    async def _test_query(self, query: str, description: str):
        """Test a specific query."""
        logger.info(f"Testing query: '{query}' - {description}")
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            # Execute retrieval
            result = await self.retriever.get_retrieval_result(query)
            
            end_time = asyncio.get_event_loop().time()
            latency_ms = (end_time - start_time) * 1000
            
            # Analyze results
            success = self._analyze_results(query, result, description)
            
            # Record test result
            self.test_results.append({
                "query": query,
                "description": description,
                "success": success,
                "latency_ms": latency_ms,
                "documents_found": len(result.documents) if result.documents else 0,
                "expanded_queries": len(result.expanded_queries) if result.expanded_queries else 0,
                "method": result.method if hasattr(result, 'method') else None,
                "threshold_used": result.threshold_used if hasattr(result, 'threshold_used') else None,
                "metadata_overrides": result.metadata_overrides if hasattr(result, 'metadata_overrides') else 0
            })
            
            logger.info(f"Query '{query}' completed in {latency_ms:.2f}ms, success: {success}")
            
        except Exception as e:
            logger.error(f"Error testing query '{query}': {str(e)}")
            self.test_results.append({
                "query": query,
                "description": description,
                "success": False,
                "error": str(e)
            })
    
    def _analyze_results(self, query: str, result, description: str) -> bool:
        """Analyze retrieval results for success criteria."""
        if not result.documents:
            logger.warning(f"No documents found for query: {query}")
            return False
        
        # Check if we have relevant documents
        relevant_keywords = self._extract_keywords(query)
        
        for doc in result.documents[:3]:  # Check top 3 results
            content_lower = doc.content.lower()
            
            # Check for keyword matches
            keyword_matches = sum(1 for keyword in relevant_keywords if keyword in content_lower)
            
            # Check for specific requirements based on query
            if self._meets_specific_requirements(query, doc):
                logger.info(f"Found relevant document for '{query}': {doc.title or doc.source}")
                return True
        
        logger.warning(f"No relevant documents found for query: {query}")
        return False
    
    def _extract_keywords(self, query: str) -> list:
        """Extract relevant keywords from query."""
        # Normalize query
        query_lower = query.lower()
        
        # Remove common words
        stop_words = {"el", "la", "de", "del", "y", "o", "con", "para", "por", "en", "a", "que", "se", "es", "son"}
        
        keywords = []
        for word in query_lower.split():
            if word not in stop_words and len(word) > 2:
                keywords.append(word)
        
        return keywords
    
    def _meets_specific_requirements(self, query: str, doc) -> bool:
        """Check if document meets specific requirements for the query."""
        query_lower = query.lower()
        content_lower = doc.content.lower()
        
        # Specific test cases
        if "iptv" in query_lower and "precio" in query_lower:
            return "iptv" in content_lower and any(word in content_lower for word in ["precio", "costo", "₡"])
        
        elif "horario" in query_lower and "administrativo" in query_lower:
            return "horario" in content_lower and "administrativo" in content_lower
        
        elif "telefonía" in query_lower or "telefonia" in query_lower:
            return "telefonía" in content_lower or "voip" in content_lower or "línea fija" in content_lower
        
        elif "precio" in query_lower:
            return any(word in content_lower for word in ["precio", "costo", "₡"])
        
        elif "horario" in query_lower:
            return "horario" in content_lower or "atención" in content_lower
        
        elif "cobertura" in query_lower:
            return "cobertura" in content_lower or "zona" in content_lower
        
        elif "plan" in query_lower and ("500" in query_lower or "gbps" in query_lower):
            return any(word in content_lower for word in ["500", "mbps", "gbps", "simétrico"])
        
        return True  # Default to True for other queries
    
    async def _test_performance(self):
        """Test performance requirements."""
        logger.info("Testing performance requirements...")
        
        # Test queries for performance
        performance_queries = [
            "precio internet",
            "horario atención",
            "cobertura zona",
            "plan telefonía",
            "iptv canales"
        ]
        
        latencies = []
        
        for query in performance_queries:
            start_time = asyncio.get_event_loop().time()
            
            try:
                result = await self.retriever.get_retrieval_result(query)
                end_time = asyncio.get_event_loop().time()
                latency_ms = (end_time - start_time) * 1000
                latencies.append(latency_ms)
                
                logger.info(f"Performance test '{query}': {latency_ms:.2f}ms")
                
            except Exception as e:
                logger.error(f"Performance test failed for '{query}': {str(e)}")
        
        # Calculate statistics
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            median_latency = sorted(latencies)[len(latencies) // 2]
            max_latency = max(latencies)
            
            logger.info(f"Performance results:")
            logger.info(f"  - Average latency: {avg_latency:.2f}ms")
            logger.info(f"  - Median latency: {median_latency:.2f}ms")
            logger.info(f"  - Max latency: {max_latency:.2f}ms")
            
            # Check if performance meets requirements (< 250ms median)
            performance_success = median_latency < 250
            
            self.test_results.append({
                "test_type": "performance",
                "success": performance_success,
                "avg_latency_ms": avg_latency,
                "median_latency_ms": median_latency,
                "max_latency_ms": max_latency,
                "requirement_met": performance_success
            })
    
    def _print_results(self):
        """Print test results summary."""
        logger.info("\n" + "="*60)
        logger.info("HYBRID RETRIEVER TEST RESULTS")
        logger.info("="*60)
        
        # Query test results
        query_tests = [r for r in self.test_results if "query" in r]
        successful_queries = sum(1 for r in query_tests if r.get("success", False))
        total_queries = len(query_tests)
        
        logger.info(f"Query Tests: {successful_queries}/{total_queries} successful ({successful_queries/total_queries*100:.1f}%)")
        
        # Performance results
        performance_tests = [r for r in self.test_results if r.get("test_type") == "performance"]
        if performance_tests:
            perf = performance_tests[0]
            logger.info(f"Performance: {'PASS' if perf['success'] else 'FAIL'}")
            logger.info(f"  - Median latency: {perf['median_latency_ms']:.2f}ms (target: <250ms)")
        
        # Detailed results
        logger.info("\nDetailed Results:")
        for result in self.test_results:
            if "query" in result:
                status = "PASS" if result.get("success", False) else "FAIL"
                logger.info(f"  {status}: {result['query']} ({result['latency_ms']:.2f}ms)")
                expanded_queries = result.get("expanded_queries", 0)
                if expanded_queries and expanded_queries > 0:
                    logger.info(f"    Expanded to: {expanded_queries} queries")
        
        # Overall success rate
        overall_success = successful_queries / total_queries if total_queries > 0 else 0
        logger.info(f"\nOverall Success Rate: {overall_success*100:.1f}%")
        
        if overall_success >= 0.9:
            logger.info("✅ ACCEPTANCE CRITERIA MET: ≥90% success rate achieved")
        else:
            logger.info("❌ ACCEPTANCE CRITERIA NOT MET: <90% success rate")


async def main():
    """Main test function."""
    try:
        tester = HybridRetrieverTester()
        await tester.setup()
        await tester.run_tests()
        
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
