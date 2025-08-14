/**
 * Hook for managing unread messages in conversations.
 * Handles real-time updates, automatic marking as read, and unread count tracking.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/lib/store';
import { wsClient as globalWsClient } from '@/lib/ws';
import { messageQueryKeys } from '@/features/messages/hooks/useMessages';

interface UseUnreadMessagesOptions {
  conversationId: string;
  autoMarkAsRead?: boolean; // Whether to automatically mark messages as read when viewing
  enabled?: boolean; // Whether the hook should be active
  wsClient?: any; // WebSocket client instance
}

export function useUnreadMessages({
  conversationId,
  autoMarkAsRead = true,
  enabled = true,
  wsClient: providedWsClient
}: UseUnreadMessagesOptions) {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const [unreadCount, setUnreadCount] = useState(0);
  const [hasMarkedAsRead, setHasMarkedAsRead] = useState(false);
  const [isVisible, setIsVisible] = useState(true);
  const markAsReadTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Use provided WebSocket client or fall back to global one
  const wsClient = providedWsClient || globalWsClient;

  console.log('🔧 [UNREAD] Hook initialized:', { 
    conversationId, 
    autoMarkAsRead, 
    enabled, 
    user: !!user, 
    wsClient: !!wsClient,
    providedWsClient: !!providedWsClient,
    globalWsClient: !!globalWsClient,
    wsClientType: wsClient?.constructor?.name
  });

  // Calculate unread messages count from query cache
  const calculateUnreadCount = useCallback(() => {
    if (!conversationId) return 0;

    const queryData = queryClient.getQueryData(
      messageQueryKeys.conversationMessages(conversationId, { limit: 50 })
    );

    if (!queryData || typeof queryData !== 'object') {
      console.log('📊 [UNREAD] No query data available for conversation:', conversationId);
      return 0;
    }

    const data = queryData as { pages: { messages: any[] }[] };
    const allMessages = data.pages.flatMap(page => page.messages || []);

    console.log('📊 [UNREAD] Total messages in cache:', allMessages.length);

    // Count inbound messages that are not read and are from customers (not agents)
    const unreadInboundMessages = allMessages.filter(
      (message) => {
        const isUnread = message.direction === 'inbound' && 
                        message.status !== 'read' &&
                        message.sender_role === 'customer';
        
        if (isUnread) {
          console.log('📊 [UNREAD] Found unread message:', {
            id: message._id,
            direction: message.direction,
            status: message.status,
            sender_role: message.sender_role,
            text: message.text_content?.substring(0, 50)
          });
        }
        
        return isUnread;
      }
    );

    console.log('📊 [UNREAD] Unread inbound messages count:', unreadInboundMessages.length);
    return unreadInboundMessages.length;
  }, [conversationId, queryClient]);

  // Mark messages as read
  const markMessagesAsRead = useCallback(async () => {
    if (!conversationId || !user || hasMarkedAsRead) return;

    try {
      console.log('📖 [UNREAD] Marking messages as read for conversation:', conversationId);
      console.log('📖 [UNREAD] WebSocket connected:', wsClient.isConnected);
      console.log('📖 [UNREAD] WebSocket readyState:', wsClient.wsInstance?.readyState);
      console.log('📖 [UNREAD] User ID:', user._id);
      
      // Wait for WebSocket to be connected
      if (!wsClient.isConnected) {
        console.log('⏳ [UNREAD] Waiting for WebSocket connection...');
        // Wait up to 5 seconds for connection
        for (let i = 0; i < 50; i++) {
          await new Promise(resolve => setTimeout(resolve, 100));
          if (wsClient.isConnected) {
            console.log('✅ [UNREAD] WebSocket connected, proceeding...');
            break;
          }
        }
        
        if (!wsClient.isConnected) {
          console.warn('⚠️ [UNREAD] WebSocket not connected after waiting, proceeding with HTTP only');
        }
      }
      
      // Send WebSocket message to mark messages as read
      console.log('📤 [UNREAD] About to send WebSocket message...');
      wsClient.markMessagesAsRead(conversationId);
      
      setHasMarkedAsRead(true);
      setUnreadCount(0);
      setIsVisible(false);
      
      // Invalidate messages query to refresh status
      queryClient.invalidateQueries({
        queryKey: messageQueryKeys.conversationMessages(conversationId, { limit: 50 })
      });
      
      console.log('✅ [UNREAD] Messages marked as read successfully');
    } catch (error) {
      console.error('❌ [UNREAD] Failed to mark messages as read:', error);
    }
  }, [conversationId, user, hasMarkedAsRead, queryClient]);

  // Auto-mark as read when agent views conversation
  useEffect(() => {
    if (!enabled || !autoMarkAsRead || !conversationId || !user) {
      console.log('🚫 [UNREAD] Auto-mark as read disabled:', { enabled, autoMarkAsRead, conversationId, user: !!user });
      return;
    }

    console.log('🔄 [UNREAD] Setting up auto-mark as read for conversation:', conversationId);

    // Clear any existing timeout
    if (markAsReadTimeoutRef.current) {
      clearTimeout(markAsReadTimeoutRef.current);
    }

    // Mark as read after a short delay to ensure messages are loaded
    markAsReadTimeoutRef.current = setTimeout(() => {
      console.log('⏰ [UNREAD] Auto-mark as read timeout triggered for conversation:', conversationId);
      markMessagesAsRead();
    }, 1000); // 1 second delay

    return () => {
      if (markAsReadTimeoutRef.current) {
        clearTimeout(markAsReadTimeoutRef.current);
      }
    };
  }, [enabled, autoMarkAsRead, conversationId, user, markMessagesAsRead]);

  // Update unread count when messages change
  useEffect(() => {
    if (!enabled) return;

    const count = calculateUnreadCount();
    setUnreadCount(count);
    
    // Show banner if there are unread messages and we haven't marked them as read
    setIsVisible(count > 0 && !hasMarkedAsRead);
    
    console.log(`📊 [UNREAD] Unread count updated: ${count} messages`);
  }, [enabled, calculateUnreadCount, hasMarkedAsRead]);

  // WebSocket message handlers
  useEffect(() => {
    if (!enabled || !conversationId) return;

    // Handle messages read confirmation
    const unsubscribeMessagesRead = wsClient.subscribe('messages_read_confirmed', (message: any) => {
      if (message.conversation_id === conversationId) {
        console.log('✅ [UNREAD] Received messages read confirmation:', message);
        setUnreadCount(0);
        setIsVisible(false);
        setHasMarkedAsRead(true);
        
        // Invalidate messages query to refresh status
        queryClient.invalidateQueries({
          queryKey: messageQueryKeys.conversationMessages(conversationId, { limit: 50 })
        });
      }
    });

    // Handle new messages
    const unsubscribeNewMessage = wsClient.subscribe('new_message', (message: any) => {
      if (message.conversation_id === conversationId) {
        // If it's an inbound message and we're not currently viewing, increment unread count
        if (message.message?.direction === 'inbound' && message.message?.sender_role === 'customer') {
          console.log('📨 [UNREAD] New inbound message received');
          // Recalculate unread count
          const newCount = calculateUnreadCount();
          setUnreadCount(newCount);
          setIsVisible(newCount > 0 && !hasMarkedAsRead);
        }
      }
    });

    // Handle unread count updates
    const unsubscribeUnreadCount = wsClient.subscribe('unread_count_update', (message: any) => {
      if (message.conversation_id === conversationId) {
        console.log('📊 [UNREAD] Received unread count update:', message.unread_count);
        setUnreadCount(message.unread_count);
        setIsVisible(message.unread_count > 0 && !hasMarkedAsRead);
      }
    });

    return () => {
      unsubscribeMessagesRead();
      unsubscribeNewMessage();
      unsubscribeUnreadCount();
    };
  }, [enabled, conversationId, calculateUnreadCount, hasMarkedAsRead, queryClient]);

  // Reset state when conversation changes
  useEffect(() => {
    setHasMarkedAsRead(false);
    setIsVisible(true);
    setUnreadCount(0);
  }, [conversationId]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (markAsReadTimeoutRef.current) {
        clearTimeout(markAsReadTimeoutRef.current);
      }
    };
  }, []);

  return {
    unreadCount,
    isVisible,
    hasMarkedAsRead,
    markMessagesAsRead,
    calculateUnreadCount
  };
}
