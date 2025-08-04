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
      lastSubscribed: number;
      lastVerified: number;
      retryCount: number;
      isSubscribing: boolean;
    }
  }>({});
  const verificationTimeouts = useRef<{ [key: string]: NodeJS.Timeout }>({});

  // Verify subscription health with proper throttling
  const verifySubscription = useCallback(async (convId: string) => {
    const state = subscriptionState[convId];
    const now = Date.now();
    
    // Prevent multiple simultaneous verification attempts
    if (state?.isSubscribing) {
      console.log('🔔 [WEBSOCKET] Subscription verification already in progress for:', convId);
      return true;
    }

    // Check if recently subscribed (prevent spam)
    if (state?.lastSubscribed && (now - state.lastSubscribed) < 5000) {
      console.log('🔔 [WEBSOCKET] Recently subscribed, skipping verification for:', convId);
      return true;
    }

    // Check if subscription is still valid (long verification interval)
    if (state?.isSubscribed && state.lastVerified && (now - state.lastVerified) < 60000) {
      console.log('🔔 [WEBSOCKET] Subscription still valid for:', convId);
      return true;
    }

    // Check WebSocket connection
    if (!wsRef.current?.isConnected) {
      console.log('🔔 [WEBSOCKET] Connection lost, attempting to reconnect...');
      try {
        await wsRef.current?.connectWithAuth();
        // Wait a bit for connection to stabilize
        await new Promise(resolve => setTimeout(resolve, 1000));
      } catch (error) {
        console.error('❌ [WEBSOCKET] Reconnection failed:', error);
        
        // Implement exponential backoff for failed connections
        const retryDelay = Math.min(5000 * Math.pow(2, (state?.retryCount || 0)), 30000);
        console.log(`🔔 [WEBSOCKET] Will retry in ${retryDelay}ms`);
        
        setSubscriptionState(prev => ({
          ...prev,
          [convId]: {
            ...prev[convId],
            retryCount: (prev[convId]?.retryCount || 0) + 1,
            isSubscribing: false
          }
        }));
        
        // Schedule retry
        verificationTimeouts.current[convId] = setTimeout(() => {
          verifySubscription(convId);
        }, retryDelay);
        
        return false;
      }
    }

    // Perform subscription if needed
    console.log('🔔 [WEBSOCKET] Subscribing to conversation:', convId);
    
    setSubscriptionState(prev => ({
      ...prev,
      [convId]: {
        ...prev[convId],
        isSubscribing: true
      }
    }));

    try {
      wsRef.current?.subscribeToConversation(convId);
      
      setSubscriptionState(prev => ({
        ...prev,
        [convId]: {
          isSubscribed: true,
          lastSubscribed: now,
          lastVerified: now,
          retryCount: 0, // Reset retry count on success
          isSubscribing: false
        }
      }));
      
      return true;
    } catch (error) {
      console.error('❌ [WEBSOCKET] Subscription failed:', error);
      
      setSubscriptionState(prev => ({
        ...prev,
        [convId]: {
          ...prev[convId],
          isSubscribing: false,
          retryCount: (prev[convId]?.retryCount || 0) + 1
        }
      }));
      
      return false;
    }
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

  // Subscribe to conversation when conversationId changes (simplified)
  useEffect(() => {
    if (conversationId && wsRef.current) {
      // Clear any existing timeouts for this conversation
      if (verificationTimeouts.current[conversationId]) {
        clearTimeout(verificationTimeouts.current[conversationId]);
        delete verificationTimeouts.current[conversationId];
      }

      // Register subscription status callback
      wsRef.current.onSubscriptionStatusChange(conversationId, (isSubscribed: boolean) => {
        console.log(`🔔 [WEBSOCKET] Server confirmed subscription status for ${conversationId}:`, isSubscribed);
        setSubscriptionState(prev => ({
          ...prev,
          [conversationId]: {
            ...prev[conversationId],
            isSubscribed,
            lastVerified: Date.now(),
            isSubscribing: false,
            retryCount: 0 // Reset retry count on server confirmation
          }
        }));
      });

      // Initial subscription with small delay to ensure connection is ready
      const subscribeTimeout = setTimeout(() => {
        verifySubscription(conversationId);
      }, 500);

      return () => {
        clearTimeout(subscribeTimeout);
        
        // Clear verification timeouts
        if (verificationTimeouts.current[conversationId]) {
          clearTimeout(verificationTimeouts.current[conversationId]);
          delete verificationTimeouts.current[conversationId];
        }

        // Remove subscription status callback
        if (wsRef.current) {
          wsRef.current.offSubscriptionStatusChange(conversationId);
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

  // Simple connection monitoring (much less aggressive)
  useEffect(() => {
    if (!wsRef.current || !conversationId) return;

    const connectionCheckInterval = setInterval(() => {
      // Only re-verify if connection seems lost and we haven't verified recently
      const state = subscriptionState[conversationId];
      const now = Date.now();
      
      if (!wsRef.current?.isConnected && 
          (!state?.lastVerified || (now - state.lastVerified) > 30000)) {
        console.log('🔔 [WEBSOCKET] Connection lost, scheduling recovery...');
        
        // Clear any existing timeout
        if (verificationTimeouts.current[conversationId]) {
          clearTimeout(verificationTimeouts.current[conversationId]);
        }
        
        // Schedule verification with delay to avoid spam
        verificationTimeouts.current[conversationId] = setTimeout(() => {
          verifySubscription(conversationId);
        }, 2000);
      }
    }, 30000); // Check every 30 seconds (much less aggressive)

    return () => clearInterval(connectionCheckInterval);
  }, [conversationId, subscriptionState, verifySubscription]);

  // Clean up all timeouts on unmount
  useEffect(() => {
    return () => {
      Object.values(verificationTimeouts.current).forEach(timeout => {
        clearTimeout(timeout);
      });
      verificationTimeouts.current = {};
    };
  }, []);

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
    // Manual subscription verification (for emergency use only)
    forceResubscribe: (id: string) => {
      setSubscriptionState(prev => ({
        ...prev,
        [id]: {
          ...prev[id],
          lastVerified: 0, // Force re-verification
          isSubscribed: false
        }
      }));
      verifySubscription(id);
    }
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