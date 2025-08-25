"""
Performance monitoring endpoints for AI services.
Provides real-time metrics and health status for RAG retrieval.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.services.ai.shared.performance_monitor import performance_monitor
from app.services.ai.shared.retrieval_cache import retrieval_cache
from app.services.ai.shared.connection_pool import connection_pool
from app.services.ai.shared.test_performance import PerformanceTest
from app.core.logger import logger


router = APIRouter(prefix="/ai/performance", tags=["AI Performance"])


class PerformanceResponse(BaseModel):
    """Response model for performance data."""
    status: str
    data: Dict[str, Any]
    timestamp: str


@router.get("/health", response_model=PerformanceResponse)
async def get_ai_health():
    """Get AI system health status."""
    try:
        health_status = performance_monitor.get_health_status()
        
        return PerformanceResponse(
            status="success",
            data=health_status,
            timestamp=health_status["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"❌ [API] Failed to get AI health: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get health status: {str(e)}")


@router.get("/stats", response_model=PerformanceResponse)
async def get_performance_stats(last_minutes: int = 30):
    """Get performance statistics for the last N minutes."""
    try:
        if last_minutes < 1 or last_minutes > 1440:  # Max 24 hours
            raise HTTPException(status_code=400, detail="last_minutes must be between 1 and 1440")
        
        stats = performance_monitor.get_performance_stats(last_minutes=last_minutes)
        
        return PerformanceResponse(
            status="success",
            data=stats,
            timestamp=stats.get("timestamp", "")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API] Failed to get performance stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance stats: {str(e)}")


@router.get("/strategy-comparison", response_model=PerformanceResponse)
async def get_strategy_comparison():
    """Get performance comparison across different retrieval strategies."""
    try:
        comparison = performance_monitor.get_strategy_comparison()
        
        return PerformanceResponse(
            status="success",
            data=comparison,
            timestamp=""
        )
        
    except Exception as e:
        logger.error(f"❌ [API] Failed to get strategy comparison: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get strategy comparison: {str(e)}")


@router.get("/cache-stats", response_model=PerformanceResponse)
async def get_cache_stats():
    """Get cache system statistics."""
    try:
        cache_stats = retrieval_cache.get_cache_stats()
        
        return PerformanceResponse(
            status="success",
            data=cache_stats,
            timestamp=""
        )
        
    except Exception as e:
        logger.error(f"❌ [API] Failed to get cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


@router.get("/connection-pool", response_model=PerformanceResponse)
async def get_connection_pool_stats():
    """Get connection pool statistics."""
    try:
        pool_stats = connection_pool.get_stats()
        
        return PerformanceResponse(
            status="success",
            data=pool_stats,
            timestamp=""
        )
        
    except Exception as e:
        logger.error(f"❌ [API] Failed to get connection pool stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get connection pool stats: {str(e)}")


@router.post("/test", response_model=PerformanceResponse)
async def run_performance_test(background_tasks: BackgroundTasks):
    """Run comprehensive performance test suite."""
    try:
        # Run test in background to avoid timeout
        test_suite = PerformanceTest()
        results = await test_suite.run_comprehensive_test()
        
        return PerformanceResponse(
            status="success",
            data=results,
            timestamp=str(results["test_summary"]["timestamp"])
        )
        
    except Exception as e:
        logger.error(f"❌ [API] Performance test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Performance test failed: {str(e)}")


@router.post("/cache/clear", response_model=PerformanceResponse)
async def clear_cache():
    """Clear the retrieval cache."""
    try:
        cleared_count = retrieval_cache.clear_cache()
        
        return PerformanceResponse(
            status="success",
            data={"cleared_entries": cleared_count, "message": "Cache cleared successfully"},
            timestamp=""
        )
        
    except Exception as e:
        logger.error(f"❌ [API] Failed to clear cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.post("/connection-pool/reset", response_model=PerformanceResponse)
async def reset_connection_pool():
    """Reset the connection pool."""
    try:
        connection_pool.reset_pool()
        
        return PerformanceResponse(
            status="success",
            data={"message": "Connection pool reset successfully"},
            timestamp=""
        )
        
    except Exception as e:
        logger.error(f"❌ [API] Failed to reset connection pool: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reset connection pool: {str(e)}")


@router.post("/monitor/reset", response_model=PerformanceResponse)
async def reset_performance_monitor():
    """Reset performance monitoring statistics."""
    try:
        performance_monitor.reset_stats()
        
        return PerformanceResponse(
            status="success",
            data={"message": "Performance monitor reset successfully"},
            timestamp=""
        )
        
    except Exception as e:
        logger.error(f"❌ [API] Failed to reset performance monitor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reset performance monitor: {str(e)}")
