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
    const optimisticMessage: Message = {
      _id: `optimistic-${Date.now()}`,
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
      isOptimistic: true,
    } as Message & { isOptimistic: boolean };

    console.log('🚀 [WHATSAPP_UX] Adding optimistic message, scrolling to bottom...');

    // Always scroll to bottom for agent's own messages
    setIsAtBottom(true);
    setShowNewMessagesBanner(false);
    setNewMessagesCount(0);

    // Add optimistic message to query
    queryClient.setQueryData(
      messageQueryKeys.conversationMessages(conversationId, { limit: 50 }),
      (oldData: any) => {
        if (!oldData) return oldData;
        
        const updatedPages = [...oldData.pages];
        if (updatedPages[0]) {
          updatedPages[0] = {
            ...updatedPages[0],
            messages: [...updatedPages[0].messages, optimisticMessage]
          };
        }
        
        return {
          ...oldData,
          pages: updatedPages
        };
      }
    );

    // Immediate smooth scroll to bottom for agent messages
    setTimeout(() => {
      scrollToBottomSmooth();
    }, 50);

    return optimisticMessage._id;
  }, [conversationId, queryClient, user]);

  const updateOptimisticMessage = useCallback((optimisticId: string, realMessage: Message) => {
    console.log('✅ [WHATSAPP_UX] Updating optimistic message with real data');

    queryClient.setQueryData(
      messageQueryKeys.conversationMessages(conversationId, { limit: 50 }),
      (oldData: any) => {
        if (!oldData) return oldData;
        
        const updatedPages = oldData.pages.map((page: any) => ({
          ...page,
          messages: page.messages.map((msg: Message & { isOptimistic?: boolean }) => 
            msg._id === optimisticId 
              ? { ...realMessage, isOptimistic: false }
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
    console.log('❌ [WHATSAPP_UX] Removing failed optimistic message');

    queryClient.setQueryData(
      messageQueryKeys.conversationMessages(conversationId, { limit: 50 }),
      (oldData: any) => {
        if (!oldData) return oldData;
        
        const updatedPages = oldData.pages.map((page: any) => ({
          ...page,
          messages: page.messages.filter((msg: Message) => msg._id !== optimisticId)
        }));
        
        return {
          ...oldData,
          pages: updatedPages
        };
      }
    );
  }, [conversationId, queryClient]);

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
    if (!isInitialized || sortedMessages.length <= previousMessageCount.current) {
      previousMessageCount.current = sortedMessages.length;
      return;
    }

    const newMessagesReceived = sortedMessages.length - previousMessageCount.current;
    console.log(`📩 [WHATSAPP_UX] ${newMessagesReceived} new messages received`);

    // Check if new messages are from customer (not agent)
    const newMessages = sortedMessages.slice(-newMessagesReceived);
    const customerMessages = newMessages.filter(msg => 
      msg.direction === 'inbound' && !(msg as any).isOptimistic
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
        msg.direction === 'outbound' || (msg as any).isOptimistic
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

    previousMessageCount.current = sortedMessages.length;
  }, [
    sortedMessages.length, 
    isInitialized, 
    isAtBottom, 
    firstUnreadMessageId, 
    hasShownUnreadMarker,
    scrollToBottomSmooth
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
  }> = [];
  sortedMessages.forEach((message, index) => {
    const previousMessage = index > 0 ? sortedMessages[index - 1] : null;
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
      const unreadCount = sortedMessages
        .slice(index)
        .filter(msg => msg.direction === 'inbound').length;
      
      items.push({ 
        type: 'unread-marker', 
        count: unreadCount, 
        id: `unread-marker-${message._id}` 
      });
    }

    // Add message
    items.push({ 
      type: 'message', 
      message, 
      id: message._id || `temp-${index}`,
      isOptimistic: (message as any).isOptimistic || false
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
          const isOptimistic = item.isOptimistic || false;
          const isNewMessage = item.message!.timestamp && 
            new Date(item.message!.timestamp) > new Date(Date.now() - 3000); // Messages less than 3 seconds old
          
          return (
            <div 
              className={cn(
                "px-4 py-1",
                // Smooth push animation for new messages
                (isOptimistic || isNewMessage) && [
                  "transition-all duration-500 ease-out",
                  "animate-in slide-in-from-bottom-3 fade-in zoom-in-95"
                ]
              )}
              style={{
                // Ensure smooth animation
                transform: (isOptimistic || isNewMessage) ? 'translateY(0)' : undefined,
              }}
            >
              <MessageBubble
                key={item.id}
                message={item.message!}
                isOwn={item.message!.direction === 'outbound'}
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
