/**
 * React hook for managing WebSocket connections and real-time messaging.
 * Provides a clean interface for components to use WebSocket functionality.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/lib/store';
import { MessagingWebSocketClient, getWebSocketClient } from '@/lib/websocket';

export interface UseWebSocketOptions {
  autoConnect?: boolean;
  conversationId?: string;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { autoConnect = true, conversationId } = options;
  const queryClient = useQueryClient();
  const { user, isAuthenticated } = useAuthStore();
  const wsRef = useRef<MessagingWebSocketClient | null>(null);
  const [subscriptionState, setSubscriptionState] = useState<{
    [conversationId: string]: {
      isSubscribed: boolean;
      lastVerified: number;
      retryCount: number;
    }
  }>({});

  // Verify subscription health
  const verifySubscription = useCallback(async (convId: string) => {
    if (!wsRef.current?.isConnected) {
      console.log('🔔 [WEBSOCKET] Connection lost, attempting to reconnect...');
      try {
        await wsRef.current?.connectWithAuth();
      } catch (error) {
        console.error('❌ [WEBSOCKET] Reconnection failed:', error);
        return false;
      }
    }

    // Check if we need to re-subscribe
    const state = subscriptionState[convId];
    const now = Date.now();
    const shouldVerify = !state || 
                        !state.isSubscribed || 
                        (now - state.lastVerified) > 30000; // Verify every 30 seconds

    if (shouldVerify) {
      console.log('🔔 [WEBSOCKET] Verifying subscription for conversation:', convId);
      wsRef.current?.subscribeToConversation(convId);
      
      setSubscriptionState(prev => ({
        ...prev,
        [convId]: {
          isSubscribed: true,
          lastVerified: now,
          retryCount: (state?.retryCount || 0) + 1
        }
      }));
    }

    return true;
  }, [subscriptionState]);

  // Initialize WebSocket connection
  useEffect(() => {
    if (!isAuthenticated || !user || !autoConnect) {
      return;
    }

    const ws = getWebSocketClient(queryClient);
    wsRef.current = ws;

    // Connect with authentication - only if not already connected
    if (!ws.isConnected) {
      ws.connectWithAuth().catch((error) => {
        console.error('Failed to connect WebSocket:', error);
      });
    }

    return () => {
      // Don't disconnect on unmount since it's a global client
      // Just unsubscribe from specific conversation if needed
      if (conversationId) {
        ws.unsubscribeFromConversation(conversationId);
      }
    };
  }, [isAuthenticated, user, autoConnect, queryClient]);

  // Subscribe to conversation when conversationId changes with verification
  useEffect(() => {
    if (conversationId && wsRef.current) {
      // Initial subscription
      verifySubscription(conversationId);

      // Set up periodic verification every 30 seconds
      const verificationInterval = setInterval(() => {
        verifySubscription(conversationId);
      }, 30000);

      return () => {
        clearInterval(verificationInterval);
        if (wsRef.current) {
          wsRef.current.unsubscribeFromConversation(conversationId);
          setSubscriptionState(prev => {
            const newState = { ...prev };
            delete newState[conversationId];
            return newState;
          });
        }
      };
    }
  }, [conversationId, verifySubscription]);

  // Monitor WebSocket connection health and re-verify subscriptions
  useEffect(() => {
    if (!wsRef.current) return;

    const healthCheckInterval = setInterval(() => {
      if (wsRef.current?.isConnected) {
        // Re-verify all active subscriptions if connection is healthy
        Object.keys(subscriptionState).forEach(convId => {
          const state = subscriptionState[convId];
          const now = Date.now();
          if (state && (now - state.lastVerified) > 60000) { // Re-verify after 1 minute
            verifySubscription(convId);
          }
        });
      } else if (conversationId) {
        // Connection is down, try to reconnect and re-subscribe
        console.log('🔔 [WEBSOCKET] Connection health check failed, attempting recovery...');
        verifySubscription(conversationId);
      }
    }, 15000); // Check every 15 seconds

    return () => clearInterval(healthCheckInterval);
  }, [subscriptionState, conversationId, verifySubscription]);

  return {
    client: wsRef.current,
    isConnected: wsRef.current?.isConnected || false,
    subscribeToConversation: (id: string) => wsRef.current?.subscribeToConversation(id),
    unsubscribeFromConversation: (id: string) => wsRef.current?.unsubscribeFromConversation(id),
    sendTypingIndicator: (id: string, isTyping: boolean) => 
      wsRef.current?.sendTypingIndicator(id, isTyping),
    verifySubscription,
    subscriptionState,
    isSubscribedTo: (id: string) => subscriptionState[id]?.isSubscribed || false,
  };
}

/**
 * Hook specifically for conversation pages to handle real-time messaging
 */
export function useConversationWebSocket(conversationId: string) {
  const webSocket = useWebSocket({ 
    autoConnect: true, 
    conversationId 
  });

  const sendTypingStart = () => {
    if (conversationId) {
      webSocket.sendTypingIndicator(conversationId, true);
    }
  };

  const sendTypingStop = () => {
    if (conversationId) {
      webSocket.sendTypingIndicator(conversationId, false);
    }
  };

  return {
    ...webSocket,
    sendTypingStart,
    sendTypingStop,
  };
}