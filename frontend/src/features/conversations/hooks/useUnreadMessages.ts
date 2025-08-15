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
  const [bannerUnreadCount, setBannerUnreadCount] = useState(0); // Banner-specific count (persists independently)
  const [hasMarkedAsRead, setHasMarkedAsRead] = useState(false);
  const [hasRepliedToUnread, setHasRepliedToUnread] = useState(false); // Track if agent replied
  const [isVisible, setIsVisible] = useState(false);
  const [isCurrentlyViewing, setIsCurrentlyViewing] = useState(false);
  const markAsReadTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastViewTimeRef = useRef<number>(0);
  const initialUnreadCapturedRef = useRef<boolean>(false); // Track if we captured initial unread count

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
      setIsCurrentlyViewing(true);
      lastViewTimeRef.current = Date.now();
      // Note: Don't set setIsVisible(false) here - banner visibility is controlled separately
      
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

  // Capture initial unread count and update database unread count
  useEffect(() => {
    if (!enabled) return;

    const count = calculateUnreadCount();
    setUnreadCount(count);
    
    // CRUCIAL: Capture initial unread count for banner BEFORE auto-mark-as-read happens
    if (!initialUnreadCapturedRef.current && count > 0) {
      console.log(`🎯 [UNREAD] CAPTURING initial unread count for banner: ${count} messages`);
      setBannerUnreadCount(count);
      setIsVisible(true);
      initialUnreadCapturedRef.current = true;
    }
    
    // If no unread messages initially, hide banner
    if (count === 0 && !initialUnreadCapturedRef.current) {
      setIsVisible(false);
      initialUnreadCapturedRef.current = true;
    }
    
    console.log(`📊 [UNREAD] DB unread: ${count} | Banner: ${bannerUnreadCount} | Visible: ${isVisible} | Replied: ${hasRepliedToUnread}`);
  }, [enabled, calculateUnreadCount, conversationId, bannerUnreadCount, isVisible, hasRepliedToUnread]);

  // Banner visibility control (separate from database count)
  useEffect(() => {
    if (!enabled) return;
    
    // Banner shows when: bannerUnreadCount > 0 AND agent hasn't replied
    const shouldShowBanner = bannerUnreadCount > 0 && !hasRepliedToUnread;
    setIsVisible(shouldShowBanner);
    
    console.log(`🎯 [UNREAD] Banner visibility check: ${bannerUnreadCount} unread, replied: ${hasRepliedToUnread} → ${shouldShowBanner ? 'SHOW' : 'HIDE'}`);
  }, [enabled, bannerUnreadCount, hasRepliedToUnread]);

  // WebSocket message handlers
  useEffect(() => {
    if (!enabled || !conversationId || !wsClient) {
      console.log('🚫 [UNREAD] WebSocket handlers disabled:', { enabled, conversationId: !!conversationId, wsClient: !!wsClient });
      return;
    }

    console.log('🔗 [UNREAD] Setting up WebSocket subscriptions for conversation:', conversationId);

    // Handle messages read confirmation
    const unsubscribeMessagesRead = wsClient.subscribe('messages_read_confirmed', (message: any) => {
      if (message.conversation_id === conversationId) {
        console.log('✅ [UNREAD] Received messages read confirmation:', message);
        setUnreadCount(0); // Database count goes to 0
        setHasMarkedAsRead(true);
        setIsCurrentlyViewing(true);
        lastViewTimeRef.current = Date.now();
        
        // IMPORTANT: Do NOT hide banner here! Banner persists until agent replies
        console.log('📊 [UNREAD] Messages marked as read in backend, but banner stays visible until agent replies');
        
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
          
          // Always increment banner count for new customer messages
          setBannerUnreadCount(prev => {
            const newCount = prev + 1;
            console.log(`📨 [UNREAD] Banner count incremented: ${prev} → ${newCount}`);
            return newCount;
          });
          
          // Check if we're currently viewing this conversation
          const now = Date.now();
          const isCurrentlyViewing = (now - lastViewTimeRef.current) < 30000; // 30 seconds threshold
          
          if (isCurrentlyViewing) {
            console.log('📨 [UNREAD] Currently viewing conversation, auto-marking as read');
            // Auto-mark as read if we're currently viewing
            markMessagesAsRead();
          } else {
            console.log('📨 [UNREAD] Not currently viewing, incrementing unread count');
            // Recalculate unread count
            const newCount = calculateUnreadCount();
            setUnreadCount(newCount);
            setIsCurrentlyViewing(false);
          }
        }
        
        // If it's an outbound message from agent (reply), hide banner
        if (message.message?.direction === 'outbound' && message.message?.sender_role === 'agent') {
          console.log('📤 [UNREAD] Agent sent a reply, hiding banner');
          setHasRepliedToUnread(true);
          setBannerUnreadCount(0); // Reset banner count
          // Banner will hide automatically via the visibility effect
        }
      }
    });

    // Handle unread count updates
    const unsubscribeUnreadCount = wsClient.subscribe('unread_count_update', (message: any) => {
      if (message.conversation_id === conversationId) {
        console.log('📊 [UNREAD] Received unread count update:', message.unread_count);
        setUnreadCount(message.unread_count);
        // Don't change banner visibility here - it's controlled separately by banner logic
      }
    });

    return () => {
      unsubscribeMessagesRead();
      unsubscribeNewMessage();
      unsubscribeUnreadCount();
    };
  }, [enabled, conversationId, wsClient, queryClient, calculateUnreadCount, markMessagesAsRead]); // Include necessary stable functions

  // Reset state when conversation changes (page reload effect)
  useEffect(() => {
    setHasMarkedAsRead(false);
    setHasRepliedToUnread(false); // Reset reply status
    setIsVisible(false); // Start hidden, will show if there are unread messages
    setUnreadCount(0);
    setBannerUnreadCount(0); // Reset banner count
    setIsCurrentlyViewing(false);
    lastViewTimeRef.current = 0;
    initialUnreadCapturedRef.current = false; // Reset capture flag
    
    console.log(`🔄 [UNREAD] State reset for conversation: ${conversationId}`);
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
    bannerUnreadCount, // Separate count for banner display
    isVisible,
    hasMarkedAsRead,
    hasRepliedToUnread, // Whether agent has replied to unread messages
    isCurrentlyViewing,
    markMessagesAsRead,
    calculateUnreadCount
  };
}
