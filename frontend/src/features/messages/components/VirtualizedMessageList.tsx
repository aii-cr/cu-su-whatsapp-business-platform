/**
 * Virtualized message list component with WhatsApp-style UX
 * Features:
 * - Smooth optimistic message updates
 * - Smart auto-scroll behavior
 * - New messages banner when scrolled up
 * - Unread message marker on entry
 * - Push animations for new messages
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Virtuoso, VirtuosoHandle } from 'react-virtuoso';
import { useQueryClient } from '@tanstack/react-query';
import { Message } from '../models/message';
import { useMessages } from '../hooks/useMessages';
import { messageQueryKeys } from '../hooks/useMessages';
import { MessageBubble } from '@/features/conversations/components/MessageBubble';
import { DayBanner } from '@/features/conversations/components/DayBanner';
import { NewMessagesBanner } from './NewMessagesBanner';
import { UnreadMessageMarker } from './UnreadMessageMarker';
import { LoadingSpinner } from '@/components/feedback/LoadingSpinner';
import { EmptyState } from '@/components/feedback/EmptyState';
import { Button } from '@/components/ui/Button';
import { cn, isSameDay } from '@/lib/utils';
import { useConversationWebSocket } from '@/hooks/useWebSocket';
import { useAuthStore } from '@/lib/store';

interface VirtualizedMessageListProps {
  conversationId: string;
  className?: string;
  onSendMessage?: (text: string) => Promise<any>; // For optimistic updates
}

export function VirtualizedMessageList({ 
  conversationId, 
  className 
}: VirtualizedMessageListProps) {
  const virtuosoRef = useRef<VirtuosoHandle>(null);
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  
  // State management
  const [isInitialized, setIsInitialized] = useState(false);
  const [isAtBottom, setIsAtBottom] = useState(true);
  const [newMessagesCount, setNewMessagesCount] = useState(0);
  const [showNewMessagesBanner, setShowNewMessagesBanner] = useState(false);
  const [firstUnreadMessageId, setFirstUnreadMessageId] = useState<string | null>(null);
  const [hasShownUnreadMarker, setHasShownUnreadMarker] = useState(false);
  const [lastSeenMessageCount, setLastSeenMessageCount] = useState(0);
  const [optimisticMessages, setOptimisticMessages] = useState<Map<string, Message>>(new Map());
  
  // Refs for tracking messages and animations
  const previousMessageIds = useRef<Set<string>>(new Set());
  const newMessageIds = useRef<Set<string>>(new Set());
  
  // Data fetching
  const {
    data: messagesData,
    isLoading,
    error,
    hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
    isError,
  } = useMessages(conversationId, 50);

  // WebSocket integration
  const webSocket = useConversationWebSocket(conversationId);

  // Optimistic message functions
  const addOptimisticMessage = useCallback((text: string) => {
    const optimisticId = `optimistic-${Date.now()}-${Math.random()}`;
    const optimisticMessage: Message = {
      _id: optimisticId,
      conversation_id: conversationId,
      message_type: 'text',
      direction: 'outbound',
      sender_role: 'agent',
      sender_id: user?._id || 'current-user',
      sender_name: user?.first_name || user?.email || 'You',
      text_content: text,
      status: 'sending',
      timestamp: new Date().toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      type: 'text',
    } as Message;

    console.log('🚀 [WHATSAPP_UX] Adding optimistic message:', optimisticId);

    // Add to optimistic messages state
    setOptimisticMessages(prev => new Map(prev).set(optimisticId, optimisticMessage));

    // Always scroll to bottom for agent's own messages
    setIsAtBottom(true);
    setShowNewMessagesBanner(false);
    setNewMessagesCount(0);

    // Immediate smooth scroll to bottom for agent messages
    setTimeout(() => {
      scrollToBottomSmooth();
    }, 50);

    return optimisticId;
  }, [conversationId, user]);

  const updateOptimisticMessage = useCallback((optimisticId: string, realMessage: Message) => {
    console.log('✅ [WHATSAPP_UX] Updating optimistic message with real data:', optimisticId);

    // Remove from optimistic messages
    setOptimisticMessages(prev => {
      const newMap = new Map(prev);
      newMap.delete(optimisticId);
      return newMap;
    });

    // Update the real message in the query cache
    queryClient.setQueryData(
      messageQueryKeys.conversationMessages(conversationId, { limit: 50 }),
      (oldData: any) => {
        if (!oldData) return oldData;
        
        const updatedPages = oldData.pages.map((page: any) => ({
          ...page,
          messages: page.messages.map((msg: Message) => 
            msg._id === optimisticId 
              ? { ...realMessage, _id: realMessage._id }
              : msg
          )
        }));
        
        return {
          ...oldData,
          pages: updatedPages
        };
      }
    );
  }, [conversationId, queryClient]);

  const removeOptimisticMessage = useCallback((optimisticId: string) => {
    console.log('❌ [WHATSAPP_UX] Removing failed optimistic message:', optimisticId);

    // Remove from optimistic messages
    setOptimisticMessages(prev => {
      const newMap = new Map(prev);
      newMap.delete(optimisticId);
      return newMap;
    });
  }, []);

  // Smooth scroll to bottom function
  const scrollToBottomSmooth = useCallback(() => {
    if (virtuosoRef.current) {
      requestAnimationFrame(() => {
        virtuosoRef.current?.scrollToIndex({
          index: 'LAST',
          align: 'end',
          behavior: 'smooth'
        });
      });
    }
  }, []);

  // Handle new message banner click
  const handleNewMessagesBannerClick = useCallback(() => {
    console.log('🔄 [WHATSAPP_UX] User clicked new messages banner, scrolling to bottom');
    setShowNewMessagesBanner(false);
    setNewMessagesCount(0);
    setIsAtBottom(true);
    scrollToBottomSmooth();
  }, [scrollToBottomSmooth]);

  // Expose functions globally for conversation page
  (window as any).addOptimisticMessage = addOptimisticMessage;
  (window as any).updateOptimisticMessage = updateOptimisticMessage;
  (window as any).removeOptimisticMessage = removeOptimisticMessage;

  // Flatten messages from all pages and sort chronologically (oldest to newest)
  const messages = messagesData?.pages.flatMap((page) => page.messages) || [];
  const sortedMessages = [...messages].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  // Combine real messages with optimistic messages
  const allMessages = [...sortedMessages, ...Array.from(optimisticMessages.values())];
  const finalSortedMessages = allMessages.sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  // Handle loading older messages when user scrolls to top
  const handleStartReached = useCallback(async () => {
    if (hasNextPage && !isFetchingNextPage && isInitialized) {
      console.log('🔄 [WHATSAPP_UX] Loading older messages...');
      await fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage, isInitialized]);

  // Initialize component
  useEffect(() => {
    if (!isLoading && sortedMessages.length > 0 && !isInitialized) {
      console.log('🎯 [WHATSAPP_UX] Initializing message list');
      setIsInitialized(true);
      setLastSeenMessageCount(sortedMessages.length);
    }
  }, [isLoading, sortedMessages.length, isInitialized]);

  // Handle new messages with WhatsApp-style behavior
  const previousMessageCount = useRef(0);
  
  useEffect(() => {
    if (!isInitialized) {
      // Initialize with current message IDs
      previousMessageIds.current = new Set(finalSortedMessages.map(msg => msg._id));
      previousMessageCount.current = finalSortedMessages.length;
      return;
    }

    // Find truly new messages by comparing IDs
    const currentMessageIds = new Set(finalSortedMessages.map(msg => msg._id));
    const detectedNewMessageIds = new Set<string>();
    
    for (const messageId of currentMessageIds) {
      if (!previousMessageIds.current.has(messageId)) {
        detectedNewMessageIds.add(messageId);
      }
    }

    if (detectedNewMessageIds.size === 0) {
      previousMessageIds.current = currentMessageIds;
      return;
    }

    console.log(`📩 [WHATSAPP_UX] ${detectedNewMessageIds.size} new messages detected`);

    // Get the new messages
    const newMessages = finalSortedMessages.filter(msg => detectedNewMessageIds.has(msg._id));
    const customerMessages = newMessages.filter(msg => 
      msg.direction === 'inbound' && !optimisticMessages.has(msg._id)
    );

    if (customerMessages.length > 0) {
      console.log(`📩 [WHATSAPP_UX] ${customerMessages.length} new customer messages`);
      
      if (isAtBottom) {
        // User is at bottom - auto scroll with smooth animation
        console.log('🔄 [WHATSAPP_UX] User at bottom, auto-scrolling to new messages');
        scrollToBottomSmooth();
      } else {
        // User is scrolled up - show banner instead of auto-scroll
        console.log('📍 [WHATSAPP_UX] User scrolled up, showing new messages banner');
        setNewMessagesCount(prev => prev + customerMessages.length);
        setShowNewMessagesBanner(true);
      }

      // Mark first unread message for the entry marker
      if (!firstUnreadMessageId && !hasShownUnreadMarker) {
        setFirstUnreadMessageId(customerMessages[0]._id);
      }
    } else {
      // Agent messages - always scroll to bottom smoothly
      const agentMessages = newMessages.filter(msg => 
        msg.direction === 'outbound' || optimisticMessages.has(msg._id)
      );
      
      if (agentMessages.length > 0) {
        console.log('📤 [WHATSAPP_UX] Agent message sent, scrolling to bottom');
        setIsAtBottom(true);
        setShowNewMessagesBanner(false);
        setNewMessagesCount(0);
        setHasShownUnreadMarker(true); // Hide unread marker when agent responds
        scrollToBottomSmooth();
      }
    }

    // Update previous state and track new messages for animation
    previousMessageIds.current = currentMessageIds;
    previousMessageCount.current = finalSortedMessages.length;
    
    // Add new message IDs to animation tracking (they will be removed after animation completes)
    newMessageIds.current = new Set([...Array.from(newMessageIds.current), ...Array.from(detectedNewMessageIds)]);
    
    // Remove animation tracking after 3 seconds
    setTimeout(() => {
      newMessageIds.current = new Set();
    }, 3000);
  }, [
    finalSortedMessages, 
    isInitialized, 
    isAtBottom, 
    firstUnreadMessageId, 
    hasShownUnreadMarker,
    scrollToBottomSmooth,
    optimisticMessages
  ]);

  // Hide new messages banner when user scrolls to bottom
  useEffect(() => {
    if (isAtBottom && showNewMessagesBanner) {
      console.log('👁️ [WHATSAPP_UX] User scrolled to bottom, hiding banner');
      setShowNewMessagesBanner(false);
      setNewMessagesCount(0);
    }
  }, [isAtBottom, showNewMessagesBanner]);

  // Loading state
  if (isLoading && (!messages || messages.length === 0)) {
    return (
      <div className={cn("flex-1 flex items-center justify-center", className)}>
        <LoadingSpinner size="md" />
      </div>
    );
  }

  // Error state
  if (error || isError) {
    return (
      <div className={cn("flex-1 flex items-center justify-center", className)}>
        <EmptyState
          title="Error loading messages"
          description="Failed to load conversation messages. Please try again."
          action={
            <Button onClick={() => window.location.reload()} variant="default">
              Retry
            </Button>
          }
        />
      </div>
    );
  }

  // Empty state
  if (!messages || messages.length === 0) {
    return (
      <div className={cn("flex-1 flex items-center justify-center", className)}>
        <EmptyState
          title="No messages yet"
          description="Start the conversation by sending your first message."
        />
      </div>
    );
  }

  // Create items array with day banners and unread marker
  const items: Array<{
    type: 'day-banner' | 'unread-marker' | 'message';
    id: string;
    date?: string;
    count?: number;
    message?: Message;
    isOptimistic?: boolean;
    isNewMessage?: boolean;
  }> = [];
  
  finalSortedMessages.forEach((message, index) => {
    const previousMessage = index > 0 ? finalSortedMessages[index - 1] : null;
    const showDayBanner = !previousMessage || !isSameDay(message.timestamp, previousMessage.timestamp);
    
    // Add day banner
    if (showDayBanner) {
      items.push({ 
        type: 'day-banner', 
        date: message.timestamp, 
        id: `day-${message.timestamp}` 
      });
    }

    // Add unread marker before first unread message (only once per session)
    if (firstUnreadMessageId && 
        message._id === firstUnreadMessageId && 
        !hasShownUnreadMarker &&
        message.direction === 'inbound') {
      
      // Count unread messages from this point
      const unreadCount = finalSortedMessages
        .slice(index)
        .filter(msg => msg.direction === 'inbound').length;
      
      items.push({ 
        type: 'unread-marker', 
        count: unreadCount, 
        id: `unread-marker-${message._id}` 
      });
    }

    // Add message
    const isOptimistic = optimisticMessages.has(message._id);
    const isNewMessage = newMessageIds.current.has(message._id);
    
    items.push({ 
      type: 'message', 
      message, 
      id: message._id || `temp-${index}`,
      isOptimistic,
      isNewMessage: isNewMessage || isOptimistic
    });
  });

  return (
    <div className={cn("h-full flex flex-col bg-slate-50 dark:bg-slate-800/30", className)}>
      <Virtuoso
        ref={virtuosoRef}
        data={items}
        itemContent={(index, item) => {
          if (item.type === 'day-banner') {
            return (
              <div className="px-4 py-2">
                <DayBanner date={item.date!} />
              </div>
            );
          }

          if (item.type === 'unread-marker') {
            return (
              <div className="px-4 py-1">
                <UnreadMessageMarker count={item.count!} />
              </div>
            );
          }
          
          // Message with smooth push animation
          return (
            <div className="px-4 py-1">
              <MessageBubble
                key={item.id}
                message={item.message!}
                isOwn={item.message!.direction === 'outbound'}
                isOptimistic={item.isOptimistic}
                isNewMessage={item.isNewMessage}
              />
            </div>
          );
        }}
        startReached={handleStartReached}
        followOutput={isAtBottom ? "auto" : false}
        alignToBottom={true}
        initialTopMostItemIndex={items.length - 1}
        atBottomStateChange={setIsAtBottom}
        components={{
          Header: () => (
            <div className="flex justify-center py-2">
              {isFetchingNextPage && (
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <LoadingSpinner size="sm" />
                  Loading older messages...
                </div>
              )}
              {!hasNextPage && items.length > 0 && (
                <div className="text-xs text-muted-foreground text-center py-2">
                  Beginning of conversation
                </div>
              )}
            </div>
          ),
          Footer: () => (
            <div className="h-4" />
          ),
        }}
        className="flex-1"
        style={{ 
          visibility: isInitialized ? 'visible' : 'hidden' 
        }}
      />

      {/* Floating new messages banner */}
      {showNewMessagesBanner && newMessagesCount > 0 && (
        <NewMessagesBanner
          count={newMessagesCount}
          onClick={handleNewMessagesBannerClick}
        />
      )}
    </div>
  );
}
