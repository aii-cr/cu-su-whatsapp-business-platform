/**
 * React hook for dashboard WebSocket connection and real-time updates.
 * Manages connection, subscriptions, and state updates for the dashboard.
 */

import { useEffect, useState, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { createDashboardWebSocketClient, getDashboardWebSocketClient, DashboardWebSocketClient } from '@/lib/dashboardWebsocket';
import { useAuthStore } from '@/lib/store';

export interface DashboardWebSocketState {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  unreadCounts: Record<string, number>;
}

export function useDashboardWebSocket() {
  const queryClient = useQueryClient();
  const { isAuthenticated, user } = useAuthStore();
  const [state, setState] = useState<DashboardWebSocketState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    unreadCounts: {},
  });
  
  const clientRef = useRef<DashboardWebSocketClient | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize WebSocket client
  useEffect(() => {
    if (isAuthenticated && user && !clientRef.current) {
      console.log('🏠 [DASHBOARD_HOOK] Initializing dashboard WebSocket client');
      clientRef.current = createDashboardWebSocketClient(queryClient);
      
      // Set up event handlers for connection state
      setupConnectionHandlers();
    }
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [isAuthenticated, user, queryClient]);

  // Auto-connect when authenticated
  useEffect(() => {
    if (isAuthenticated && user && clientRef.current && !state.isConnected && !state.isConnecting) {
      console.log('🏠 [DASHBOARD_HOOK] Auto-connecting to dashboard WebSocket');
      connect();
    }
  }, [isAuthenticated, user, state.isConnected, state.isConnecting]);

  // Setup connection event handlers
  const setupConnectionHandlers = useCallback(() => {
    if (!clientRef.current) return;

    // Add handlers for unread count updates
    clientRef.current.addMessageHandler('unread_count_update', (data) => {
      setState(prev => ({
        ...prev,
        unreadCounts: {
          ...prev.unreadCounts,
          [data.conversation_id]: data.unread_count,
        },
      }));
    });

    clientRef.current.addMessageHandler('initial_unread_counts', (data) => {
      setState(prev => ({
        ...prev,
        unreadCounts: data.unread_counts,
      }));
    });
  }, []);

  const connect = useCallback(async () => {
    if (!clientRef.current || !isAuthenticated || !user) {
      console.log('🏠 [DASHBOARD_HOOK] Cannot connect: missing requirements');
      return;
    }

    if (state.isConnecting || state.isConnected) {
      console.log('🏠 [DASHBOARD_HOOK] Already connecting or connected');
      return;
    }

    setState(prev => ({ ...prev, isConnecting: true, error: null }));

    try {
      console.log('🏠 [DASHBOARD_HOOK] Connecting to dashboard WebSocket...');
      
      // Connect and subscribe to dashboard updates
      await clientRef.current.connectWithAuth();
      clientRef.current.subscribeToDashboard();
      
      setState(prev => ({ 
        ...prev, 
        isConnected: true, 
        isConnecting: false, 
        error: null 
      }));
      
      console.log('✅ [DASHBOARD_HOOK] Successfully connected to dashboard WebSocket');
    } catch (error) {
      console.error('❌ [DASHBOARD_HOOK] Failed to connect:', error);
      setState(prev => ({ 
        ...prev, 
        isConnected: false, 
        isConnecting: false, 
        error: error instanceof Error ? error.message : 'Connection failed'
      }));
      
      // Auto-retry connection after delay
      reconnectTimeoutRef.current = setTimeout(() => {
        if (isAuthenticated && user) {
          console.log('🔄 [DASHBOARD_HOOK] Retrying connection...');
          connect();
        }
      }, 5000);
    }
  }, [isAuthenticated, user, state.isConnecting, state.isConnected]);

  const disconnect = useCallback(() => {
    if (clientRef.current) {
      console.log('🏠 [DASHBOARD_HOOK] Disconnecting from dashboard WebSocket');
      clientRef.current.disconnect();
      setState(prev => ({ 
        ...prev, 
        isConnected: false, 
        isConnecting: false,
        unreadCounts: {},
      }));
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const markConversationAsRead = useCallback((conversationId: string) => {
    if (clientRef.current && state.isConnected) {
      console.log('📖 [DASHBOARD_HOOK] Marking conversation as read:', conversationId);
      clientRef.current.markConversationAsRead(conversationId);
      
      // Optimistically update local state
      setState(prev => ({
        ...prev,
        unreadCounts: {
          ...prev.unreadCounts,
          [conversationId]: 0,
        },
      }));
    }
  }, [state.isConnected]);

  const getUnreadCount = useCallback((conversationId: string): number => {
    return state.unreadCounts[conversationId] || 0;
  }, [state.unreadCounts]);

  const getTotalUnreadCount = useCallback((): number => {
    return Object.values(state.unreadCounts).reduce((total, count) => total + count, 0);
  }, [state.unreadCounts]);

  // Cleanup on unmount or auth change
  useEffect(() => {
    return () => {
      if (!isAuthenticated) {
        disconnect();
      }
    };
  }, [isAuthenticated, disconnect]);

  return {
    // Connection state
    isConnected: state.isConnected,
    isConnecting: state.isConnecting,
    error: state.error,
    
    // Unread counts
    unreadCounts: state.unreadCounts,
    getUnreadCount,
    getTotalUnreadCount,
    
    // Actions
    connect,
    disconnect,
    markConversationAsRead,
    
    // Client instance for advanced usage
    client: clientRef.current,
  };
}

export default useDashboardWebSocket;