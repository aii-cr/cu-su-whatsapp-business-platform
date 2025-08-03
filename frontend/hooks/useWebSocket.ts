/**
 * React hook for managing WebSocket connections and real-time messaging.
 * Provides a clean interface for components to use WebSocket functionality.
 */

import { useEffect, useRef } from 'react';
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

  // Subscribe to conversation when conversationId changes
  useEffect(() => {
    if (conversationId && wsRef.current) {
      wsRef.current.subscribeToConversation(conversationId);

      return () => {
        if (wsRef.current) {
          wsRef.current.unsubscribeFromConversation(conversationId);
        }
      };
    }
  }, [conversationId]);

  return {
    client: wsRef.current,
    isConnected: wsRef.current?.isConnected || false,
    subscribeToConversation: (id: string) => wsRef.current?.subscribeToConversation(id),
    unsubscribeFromConversation: (id: string) => wsRef.current?.unsubscribeFromConversation(id),
    sendTypingIndicator: (id: string, isTyping: boolean) => 
      wsRef.current?.sendTypingIndicator(id, isTyping),
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