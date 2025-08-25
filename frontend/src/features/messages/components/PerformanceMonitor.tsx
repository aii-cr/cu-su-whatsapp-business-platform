import React, { useEffect, useState } from 'react';
import { useMessagesInfiniteScroll } from '../hooks/useMessages';
import { Clock, Zap, Database, TrendingUp } from 'lucide-react';

interface PerformanceMonitorProps {
  conversationId: string;
}

interface PerformanceMetrics {
  cacheHitRate: number;
  averageLoadTime: number;
  totalMessages: number;
  cacheHits: number;
  cacheMisses: number;
  lastUpdate: Date;
}

export function PerformanceMonitor({ conversationId }: PerformanceMonitorProps) {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    cacheHitRate: 0,
    averageLoadTime: 0,
    totalMessages: 0,
    cacheHits: 0,
    cacheMisses: 0,
    lastUpdate: new Date()
  });

  const {
    data: messagesData,
    isLoading,
    isFetching
  } = useMessagesInfiniteScroll(conversationId, 50);

  useEffect(() => {
    if (messagesData?.pages) {
      const pages = messagesData.pages;
      const totalMessages = pages.reduce((acc, page) => acc + page.messages.length, 0);
      const cacheHits = pages.filter(page => page.cache_hit).length;
      const cacheMisses = pages.filter(page => !page.cache_hit).length;
      const cacheHitRate = pages.length > 0 ? (cacheHits / pages.length) * 100 : 0;

      setMetrics({
        cacheHitRate: Math.round(cacheHitRate),
        averageLoadTime: 0, // TODO: Track actual load times
        totalMessages,
        cacheHits,
        cacheMisses,
        lastUpdate: new Date()
      });
    }
  }, [messagesData]);

  if (!messagesData?.pages || messagesData.pages.length === 0) {
    return null;
  }

  return (
    <div className="fixed bottom-4 left-4 z-50">
      <div className="bg-background border border-border rounded-lg p-3 shadow-lg">
        <div className="flex items-center space-x-2 mb-2">
          <TrendingUp className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium text-foreground">Performance</span>
        </div>
        
        <div className="space-y-2">
          {/* Cache Hit Rate */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1">
              <Zap className="h-3 w-3 text-green-500" />
              <span className="text-xs text-muted-foreground">Cache Hit</span>
            </div>
            <span className="text-xs font-medium text-foreground">
              {metrics.cacheHitRate}%
            </span>
          </div>

          {/* Total Messages */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1">
              <Database className="h-3 w-3 text-blue-500" />
              <span className="text-xs text-muted-foreground">Messages</span>
            </div>
            <span className="text-xs font-medium text-foreground">
              {metrics.totalMessages}
            </span>
          </div>

          {/* Loading Status */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1">
              <Clock className="h-3 w-3 text-orange-500" />
              <span className="text-xs text-muted-foreground">Status</span>
            </div>
            <span className="text-xs font-medium text-foreground">
              {isLoading ? 'Loading...' : isFetching ? 'Fetching...' : 'Ready'}
            </span>
          </div>

          {/* Cache Stats */}
          <div className="pt-1 border-t border-border">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">Hits/Misses</span>
              <span className="text-xs font-medium text-foreground">
                {metrics.cacheHits}/{metrics.cacheMisses}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

