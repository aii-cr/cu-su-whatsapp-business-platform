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
  isConnected?: boolean; // Connection status from parent WebSocket hook
}

export function useUnreadMessages({
  conversationId,
  autoMarkAsRead = true,
  enabled = true,
  wsClient: providedWsClient,
  isConnected: providedIsConnected = false
}: UseUnreadMessagesOptions) {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const [unreadCount, setUnreadCount] = useState(0);
  const [hasMarkedAsRead, setHasMarkedAsRead] = useState(false);
  const [isVisible, setIsVisible] = useState(true);
  const [isCurrentlyViewing, setIsCurrentlyViewing] = useState(false);
  const markAsReadTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastViewTimeRef = useRef<number>(0);

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
    wsClientType: wsClient?.constructor?.name,
    providedIsConnected
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
      console.log('📖 [UNREAD] WebSocket client type:', wsClient?.constructor?.name);
      console.log('📖 [UNREAD] Provided connection status:', providedIsConnected);
      console.log('📖 [UNREAD] WebSocket client connected:', wsClient?.isConnected);
      console.log('📖 [UNREAD] WebSocket readyState:', wsClient?.wsInstance?.readyState);
      console.log('📖 [UNREAD] User ID:', user._id);
      
      // Check if we have a valid WebSocket client
      if (!wsClient) {
        console.warn('⚠️ [UNREAD] No WebSocket client available');
        return;
      }
      
      // Check WebSocket connection status
      const isWsConnected = wsClient.isConnected || providedIsConnected;
      if (!isWsConnected) {
        console.warn('⚠️ [UNREAD] WebSocket not connected, cannot mark messages as read');
        return;
      }
      
      // Send WebSocket message to mark messages as read
      console.log('📤 [UNREAD] About to send WebSocket message...');
      wsClient.markMessagesAsRead(conversationId);
      
      setHasMarkedAsRead(true);
      setUnreadCount(0);
      setIsVisible(false);
      setIsCurrentlyViewing(true);
      lastViewTimeRef.current = Date.now();
      
      // Invalidate messages query to refresh status
      queryClient.invalidateQueries({
        queryKey: messageQueryKeys.conversationMessages(conversationId, { limit: 50 })
      });
      
      console.log('✅ [UNREAD] Messages marked as read successfully');
    } catch (error) {
      console.error('❌ [UNREAD] Failed to mark messages as read:', error);
    }
  }, [conversationId, user, hasMarkedAsRead, queryClient, wsClient, providedIsConnected]);

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

    // Wait for WebSocket to be connected before marking as read
    const waitForConnection = async () => {
      console.log('⏰ [UNREAD] Auto-mark as read triggered for conversation:', conversationId);
      
      // Check if we have a valid WebSocket client
      if (!wsClient) {
        console.warn('⚠️ [UNREAD] No WebSocket client available for auto-mark as read');
        return;
      }
      
      // Check WebSocket connection status
      const isWsConnected = wsClient.isConnected || providedIsConnected;
      if (!isWsConnected) {
        console.warn('⚠️ [UNREAD] WebSocket not connected, aborting auto-mark as read');
        return;
      }
      
      // Now mark messages as read
      await markMessagesAsRead();
    };

    // Start the process after a short delay to ensure messages are loaded
    markAsReadTimeoutRef.current = setTimeout(waitForConnection, 1000); // Reduced to 1 second

    return () => {
      if (markAsReadTimeoutRef.current) {
        clearTimeout(markAsReadTimeoutRef.current);
      }
    };
  }, [enabled, autoMarkAsRead, conversationId, user, markMessagesAsRead, wsClient, providedIsConnected]);

  // Update unread count when messages change
  useEffect(() => {
    if (!enabled) return;

    const count = calculateUnreadCount();
    setUnreadCount(count);
    
    // Show banner if there are unread messages and we haven't marked them as read
    // AND we're not currently viewing the conversation
    const shouldShowBanner = count > 0 && !hasMarkedAsRead && !isCurrentlyViewing;
    setIsVisible(shouldShowBanner);
    
    console.log(`📊 [UNREAD] Unread count updated: ${count} messages`);
    console.log(`📊 [UNREAD] Banner visibility: ${shouldShowBanner ? 'Visible' : 'Hidden'}`);
    console.log(`📊 [UNREAD] Currently viewing: ${isCurrentlyViewing}`);
  }, [enabled, calculateUnreadCount, hasMarkedAsRead, isCurrentlyViewing, conversationId]);

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
        setIsCurrentlyViewing(true);
        lastViewTimeRef.current = Date.now();
        
        // Invalidate messages query to refresh status
        queryClient.invalidateQueries({
          queryKey: messageQueryKeys.conversationMessages(conversationId, { limit: 50 })
        });
      }
    });

    // Handle new messages
    const unsubscribeNewMessage = wsClient.subscribe('new_message', (message: any) => {
      if (message.conversation_id === conversationId) {
        // If it's an inbound message from customer
        if (message.message?.direction === 'inbound' && message.message?.sender_role === 'customer') {
          console.log('📨 [UNREAD] New inbound message received');
          
          // Check if we're currently viewing this conversation
          const now = Date.now();
          const isCurrentlyViewing = (now - lastViewTimeRef.current) < 30000; // 30 seconds threshold
          
          if (isCurrentlyViewing) {
            console.log('📨 [UNREAD] Currently viewing conversation, auto-marking as read');
            // Auto-mark as read if we're currently viewing
            markMessagesAsRead();
          } else {
            console.log('📨 [UNREAD] Not currently viewing, incrementing unread count');
            // Recalculate unread count and show banner
            const newCount = calculateUnreadCount();
            setUnreadCount(newCount);
            setIsVisible(newCount > 0 && !hasMarkedAsRead);
            setIsCurrentlyViewing(false);
          }
        }
      }
    });

    // Handle unread count updates
    const unsubscribeUnreadCount = wsClient.subscribe('unread_count_update', (message: any) => {
      if (message.conversation_id === conversationId) {
        console.log('📊 [UNREAD] Received unread count update:', message.unread_count);
        setUnreadCount(message.unread_count);
        setIsVisible(message.unread_count > 0 && !hasMarkedAsRead && !isCurrentlyViewing);
      }
    });

    return () => {
      unsubscribeMessagesRead();
      unsubscribeNewMessage();
      unsubscribeUnreadCount();
    };
  }, [enabled, conversationId, calculateUnreadCount, hasMarkedAsRead, isCurrentlyViewing, queryClient, markMessagesAsRead]);

  // Reset state when conversation changes
  useEffect(() => {
    setHasMarkedAsRead(false);
    setIsVisible(true);
    setUnreadCount(0);
    setIsCurrentlyViewing(false);
    lastViewTimeRef.current = 0;
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
    isCurrentlyViewing,
    markMessagesAsRead,
    calculateUnreadCount
  };
}
