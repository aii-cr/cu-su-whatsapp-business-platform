"""
Performance testing and validation script for optimized RAG retrieval.
Tests both speed improvements and quality maintenance.
"""

import asyncio
import time
from typing import List, Dict, Any
import statistics

from app.services.ai.shared.tools.rag.retriever import retrieve_information
from app.services.ai.shared.performance_monitor import performance_monitor
from app.services.ai.shared.retrieval_cache import retrieval_cache
from app.services.ai.shared.connection_pool import connection_pool
from app.core.logger import logger


# Test queries representing different complexity levels
TEST_QUERIES = [
    # Simple/Fast queries
    "hola",
    "precios",
    "planes",
    "servicio",
    "cobertura",
    
    # Medium complexity queries
    "¿Qué planes de internet tienen?",
    "¿Cuánto cuesta el servicio de IPTV?",
    "¿Tienen cobertura en mi área?",
    "Información sobre addons",
    
    # Complex queries
    "¿Cuáles son los diferentes planes de internet disponibles y sus precios?",
    "¿Cómo puedo contratar el servicio de IPTV junto con internet?",
    "¿Qué documentos necesito para contratar el servicio y cuál es el proceso?",
    "¿Tienen promociones especiales para nuevos clientes?",
]


class PerformanceTest:
    """Performance testing suite for RAG retrieval."""
    
    def __init__(self):
        self.results = []
        self.baseline_times = {}
        
    async def run_single_test(self, query: str, test_name: str = "") -> Dict[str, Any]:
        """Run a single performance test."""
        start_time = time.time()
        
        try:
            result = await retrieve_information(query)
            end_time = time.time()
            
            execution_time = (end_time - start_time) * 1000  # Convert to ms
            success = not any(error_signal in result for error_signal in [
                "NO_CONTEXT_AVAILABLE", "ERROR_ACCESSING_KNOWLEDGE"
            ])
            
            return {
                "query": query,
                "test_name": test_name,
                "execution_time_ms": execution_time,
                "success": success,
                "result_length": len(result),
                "result_preview": result[:100] + "..." if len(result) > 100 else result,
                "timestamp": time.time()
            }
            
        except Exception as e:
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            
            return {
                "query": query,
                "test_name": test_name,
                "execution_time_ms": execution_time,
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def run_cache_test(self) -> Dict[str, Any]:
        """Test cache performance with repeated queries."""
        logger.info("🧪 [TEST] Running cache performance test...")
        
        test_query = "¿Qué planes de internet tienen?"
        
        # First call (cache miss)
        result1 = await self.run_single_test(test_query, "cache_miss")
        
        # Second call (should be cache hit)
        result2 = await self.run_single_test(test_query, "cache_hit")
        
        # Third call (should also be cache hit)
        result3 = await self.run_single_test(test_query, "cache_hit_2")
        
        cache_improvement = result1["execution_time_ms"] / result2["execution_time_ms"] if result2["execution_time_ms"] > 0 else 1
        
        return {
            "test_type": "cache_performance",
            "cache_miss_time_ms": result1["execution_time_ms"],
            "cache_hit_time_ms": result2["execution_time_ms"],
            "cache_hit_2_time_ms": result3["execution_time_ms"],
            "improvement_factor": cache_improvement,
            "all_successful": all([result1["success"], result2["success"], result3["success"]])
        }
    
    async def run_strategy_comparison_test(self) -> Dict[str, Any]:
        """Test different query strategies."""
        logger.info("🧪 [TEST] Running strategy comparison test...")
        
        # Test simple queries (should use fast strategy)
        simple_queries = ["hola", "precios", "planes"]
        simple_results = []
        
        for query in simple_queries:
            result = await self.run_single_test(query, "simple_query")
            simple_results.append(result)
        
        # Test complex queries (should use comprehensive strategy)
        complex_queries = [
            "¿Cuáles son los diferentes planes de internet disponibles y sus precios?",
            "¿Cómo puedo contratar el servicio de IPTV junto con internet?",
            "¿Qué documentos necesito para contratar el servicio?"
        ]
        complex_results = []
        
        for query in complex_queries:
            result = await self.run_single_test(query, "complex_query")
            complex_results.append(result)
        
        # Calculate averages
        simple_avg_time = statistics.mean([r["execution_time_ms"] for r in simple_results if r["success"]])
        complex_avg_time = statistics.mean([r["execution_time_ms"] for r in complex_results if r["success"]])
        
        return {
            "test_type": "strategy_comparison",
            "simple_queries_avg_time_ms": simple_avg_time,
            "complex_queries_avg_time_ms": complex_avg_time,
            "simple_success_rate": sum(1 for r in simple_results if r["success"]) / len(simple_results),
            "complex_success_rate": sum(1 for r in complex_results if r["success"]) / len(complex_results),
            "simple_results": simple_results,
            "complex_results": complex_results
        }
    
    async def run_load_test(self, concurrent_requests: int = 5) -> Dict[str, Any]:
        """Test performance under concurrent load."""
        logger.info(f"🧪 [TEST] Running load test with {concurrent_requests} concurrent requests...")
        
        # Select a mix of queries for load testing
        test_queries = TEST_QUERIES[:concurrent_requests]
        
        # Run concurrent requests
        start_time = time.time()
        tasks = [self.run_single_test(query, f"load_test_{i}") for i, query in enumerate(test_queries)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Process results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success", False)]
        failed_results = [r for r in results if not (isinstance(r, dict) and r.get("success", False))]
        
        if successful_results:
            avg_time = statistics.mean([r["execution_time_ms"] for r in successful_results])
            max_time = max([r["execution_time_ms"] for r in successful_results])
            min_time = min([r["execution_time_ms"] for r in successful_results])
        else:
            avg_time = max_time = min_time = 0
        
        return {
            "test_type": "load_test",
            "concurrent_requests": concurrent_requests,
            "total_time_ms": (end_time - start_time) * 1000,
            "successful_requests": len(successful_results),
            "failed_requests": len(failed_results),
            "success_rate": len(successful_results) / len(results),
            "avg_response_time_ms": avg_time,
            "max_response_time_ms": max_time,
            "min_response_time_ms": min_time,
            "requests_per_second": len(results) / (end_time - start_time)
        }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all performance tests."""
        logger.info("🚀 [TEST] Starting comprehensive performance test suite...")
        
        # Clear cache for clean test
        retrieval_cache.clear_cache()
        
        # Reset performance monitor
        performance_monitor.reset_stats()
        
        # Run individual tests
        cache_test = await self.run_cache_test()
        strategy_test = await self.run_strategy_comparison_test()
        load_test = await self.run_load_test(concurrent_requests=3)
        
        # Get overall statistics
        overall_stats = performance_monitor.get_performance_stats(last_minutes=60)
        health_status = performance_monitor.get_health_status()
        connection_stats = connection_pool.get_stats()
        cache_stats = retrieval_cache.get_cache_stats()
        
        return {
            "test_summary": {
                "total_tests_run": 3,
                "timestamp": time.time(),
                "overall_health": health_status["status"]
            },
            "cache_performance": cache_test,
            "strategy_comparison": strategy_test,
            "load_performance": load_test,
            "system_stats": {
                "performance_monitor": overall_stats,
                "connection_pool": connection_stats,
                "cache_system": cache_stats,
                "health_status": health_status
            }
        }


async def main():
    """Run the performance test suite."""
    test_suite = PerformanceTest()
    
    try:
        logger.info("🧪 [TEST] Starting RAG performance test suite...")
        results = await test_suite.run_comprehensive_test()
        
        # Print summary
        logger.info("=" * 80)
        logger.info("🎯 [TEST] PERFORMANCE TEST RESULTS SUMMARY")
        logger.info("=" * 80)
        
        # Cache performance
        cache_perf = results["cache_performance"]
        logger.info(f"📈 Cache Performance:")
        logger.info(f"  - Cache Miss Time: {cache_perf['cache_miss_time_ms']:.0f}ms")
        logger.info(f"  - Cache Hit Time: {cache_perf['cache_hit_time_ms']:.0f}ms")
        logger.info(f"  - Improvement Factor: {cache_perf['improvement_factor']:.1f}x")
        
        # Strategy comparison
        strategy_perf = results["strategy_comparison"]
        logger.info(f"🎯 Strategy Performance:")
        logger.info(f"  - Simple Queries Avg: {strategy_perf['simple_queries_avg_time_ms']:.0f}ms")
        logger.info(f"  - Complex Queries Avg: {strategy_perf['complex_queries_avg_time_ms']:.0f}ms")
        logger.info(f"  - Simple Success Rate: {strategy_perf['simple_success_rate']:.1%}")
        logger.info(f"  - Complex Success Rate: {strategy_perf['complex_success_rate']:.1%}")
        
        # Load performance
        load_perf = results["load_performance"]
        logger.info(f"🚀 Load Performance:")
        logger.info(f"  - Concurrent Requests: {load_perf['concurrent_requests']}")
        logger.info(f"  - Success Rate: {load_perf['success_rate']:.1%}")
        logger.info(f"  - Avg Response Time: {load_perf['avg_response_time_ms']:.0f}ms")
        logger.info(f"  - Requests/Second: {load_perf['requests_per_second']:.1f}")
        
        # System health
        health = results["system_stats"]["health_status"]
        logger.info(f"🏥 System Health: {health['status'].upper()} - {health['message']}")
        
        logger.info("=" * 80)
        logger.info("✅ [TEST] Performance test suite completed successfully!")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ [TEST] Performance test suite failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
