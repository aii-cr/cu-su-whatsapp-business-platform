"""
Performance monitoring and metrics for RAG retrieval system.
Provides detailed timing and quality metrics for optimization.
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
from threading import Lock

from app.core.logger import logger


@dataclass
class RetrievalMetrics:
    """Metrics for a single retrieval operation."""
    query: str
    strategy: str
    total_time_ms: float
    cache_hit: bool
    documents_found: int
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "query_length": len(self.query),
            "strategy": self.strategy,
            "total_time_ms": self.total_time_ms,
            "cache_hit": self.cache_hit,
            "documents_found": self.documents_found,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
            "success": self.error is None
        }


class PerformanceMonitor:
    """Thread-safe performance monitoring for RAG operations."""
    
    def __init__(self, max_history: int = 1000):
        """Initialize performance monitor with history limit."""
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.strategy_stats: Dict[str, List[float]] = defaultdict(list)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.cache_stats = {"hits": 0, "misses": 0}
        self._lock = Lock()
        
        logger.info(f"🔍 [MONITOR] Performance monitor initialized (max_history: {max_history})")
    
    def record_retrieval(self, metrics: RetrievalMetrics) -> None:
        """Record retrieval metrics."""
        with self._lock:
            # Add to history
            self.metrics_history.append(metrics)
            
            # Update strategy stats
            if metrics.error is None:
                self.strategy_stats[metrics.strategy].append(metrics.total_time_ms)
                
                # Limit strategy stats to prevent memory growth
                if len(self.strategy_stats[metrics.strategy]) > 100:
                    self.strategy_stats[metrics.strategy] = self.strategy_stats[metrics.strategy][-50:]
            
            # Update error counts
            if metrics.error:
                self.error_counts[metrics.error] += 1
            
            # Update cache stats
            if metrics.cache_hit:
                self.cache_stats["hits"] += 1
            else:
                self.cache_stats["misses"] += 1
        
        # Log performance for monitoring
        if metrics.error:
            logger.warning(f"⚠️ [MONITOR] Retrieval failed: {metrics.error} (query: '{metrics.query[:50]}...')")
        elif metrics.total_time_ms > 5000:  # Log slow queries
            logger.warning(f"🐌 [MONITOR] Slow retrieval: {metrics.total_time_ms:.0f}ms (strategy: {metrics.strategy})")
        else:
            logger.debug(f"✅ [MONITOR] Retrieval: {metrics.total_time_ms:.0f}ms (strategy: {metrics.strategy}, docs: {metrics.documents_found})")
    
    def get_performance_stats(self, last_minutes: int = 30) -> Dict[str, Any]:
        """Get performance statistics for the last N minutes."""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(minutes=last_minutes)
            recent_metrics = [
                m for m in self.metrics_history 
                if m.timestamp >= cutoff_time
            ]
            
            if not recent_metrics:
                return {"period_minutes": last_minutes, "total_queries": 0}
            
            # Calculate basic stats
            total_queries = len(recent_metrics)
            successful_queries = [m for m in recent_metrics if m.error is None]
            failed_queries = [m for m in recent_metrics if m.error is not None]
            
            # Timing stats for successful queries
            if successful_queries:
                times = [m.total_time_ms for m in successful_queries]
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                p95_time = sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else times[0]
            else:
                avg_time = min_time = max_time = p95_time = 0
            
            # Strategy breakdown
            strategy_breakdown = defaultdict(int)
            for m in recent_metrics:
                strategy_breakdown[m.strategy] += 1
            
            # Cache performance
            cache_hits = sum(1 for m in recent_metrics if m.cache_hit)
            cache_hit_rate = (cache_hits / total_queries * 100) if total_queries > 0 else 0
            
            # Error breakdown
            error_breakdown = defaultdict(int)
            for m in failed_queries:
                error_breakdown[m.error or "unknown"] += 1
            
            return {
                "period_minutes": last_minutes,
                "total_queries": total_queries,
                "successful_queries": len(successful_queries),
                "failed_queries": len(failed_queries),
                "success_rate_percent": (len(successful_queries) / total_queries * 100) if total_queries > 0 else 0,
                "timing_stats_ms": {
                    "average": round(avg_time, 2),
                    "minimum": round(min_time, 2),
                    "maximum": round(max_time, 2),
                    "p95": round(p95_time, 2)
                },
                "cache_performance": {
                    "hit_rate_percent": round(cache_hit_rate, 2),
                    "hits": cache_hits,
                    "misses": total_queries - cache_hits
                },
                "strategy_breakdown": dict(strategy_breakdown),
                "error_breakdown": dict(error_breakdown)
            }
    
    def get_strategy_comparison(self) -> Dict[str, Dict[str, float]]:
        """Compare performance across strategies."""
        with self._lock:
            comparison = {}
            
            for strategy, times in self.strategy_stats.items():
                if times:
                    comparison[strategy] = {
                        "avg_time_ms": sum(times) / len(times),
                        "min_time_ms": min(times),
                        "max_time_ms": max(times),
                        "sample_count": len(times)
                    }
            
            return comparison
    
    def reset_stats(self) -> None:
        """Reset all statistics."""
        with self._lock:
            self.metrics_history.clear()
            self.strategy_stats.clear()
            self.error_counts.clear()
            self.cache_stats = {"hits": 0, "misses": 0}
        
        logger.info("🔄 [MONITOR] Performance statistics reset")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status based on recent performance."""
        stats = self.get_performance_stats(last_minutes=10)
        
        # Determine health status
        if stats["total_queries"] == 0:
            status = "unknown"
            message = "No queries in the last 10 minutes"
        elif stats["success_rate_percent"] >= 95:
            if stats["timing_stats_ms"]["p95"] <= 3000:  # 3 seconds P95
                status = "healthy"
                message = "Performance is optimal"
            else:
                status = "degraded"
                message = "Performance is slower than expected"
        elif stats["success_rate_percent"] >= 80:
            status = "degraded"
            message = "Some queries are failing"
        else:
            status = "unhealthy"
            message = "High failure rate detected"
        
        return {
            "status": status,
            "message": message,
            "recent_stats": stats,
            "timestamp": datetime.now().isoformat()
        }


# Global performance monitor instance
performance_monitor = PerformanceMonitor()
