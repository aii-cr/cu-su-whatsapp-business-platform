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
  
  // Optimistic messages state for immediate rendering
  const [optimisticMessages, setOptimisticMessages] = useState<Map<string, any>>(new Map());
  
  // Ref for optimistic messages to avoid dependency issues
  const optimisticMessagesRef = useRef<Map<string, any>>(new Map());
  
  // Keep ref in sync with state
  useEffect(() => {
    optimisticMessagesRef.current = optimisticMessages;
  }, [optimisticMessages]);
  
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

  // Flatten messages from all pages and sort chronologically (oldest to newest)
  const messages = messagesData?.pages.flatMap((page) => page.messages) || [];
  
  // Add optimistic messages to the messages array
  const optimisticMessagesArray = Array.from(optimisticMessages.values());
  const allMessages = [...messages, ...optimisticMessagesArray];
  
  const sortedMessages = [...allMessages].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );
  
  // Determine if we have any messages at all (including optimistic ones)
  const hasAnyMessages = sortedMessages.length > 0;
  
  // Debug logging
  console.log('🔍 [MESSAGES] Total messages loaded:', sortedMessages.length);
  console.log('🔍 [MESSAGES] Optimistic messages:', optimisticMessagesArray.length);
  if (sortedMessages.length > 0) {
    console.log('🔍 [MESSAGES] Latest message:', sortedMessages[sortedMessages.length - 1]);
    console.log('🔍 [MESSAGES] Message IDs:', sortedMessages.map(m => m._id));
  }

  // Debug: Log when messages change
  useEffect(() => {
    console.log('🔍 [MESSAGES] Messages updated:', {
      count: sortedMessages.length,
      ids: sortedMessages.map(m => m._id),
      latest: sortedMessages[sortedMessages.length - 1]?.text_content,
      optimisticCount: optimisticMessagesArray.length,
      optimisticIds: optimisticMessagesArray.map(m => m._id)
    });
  }, [sortedMessages, optimisticMessagesArray]);

  // Debug: Log optimistic messages state changes
  useEffect(() => {
    console.log('🔍 [OPTIMISTIC_STATE] Optimistic messages state changed:', {
      count: optimisticMessages.size,
      ids: Array.from(optimisticMessages.keys()),
      messages: Array.from(optimisticMessages.values()).map(m => ({ id: m._id, text: m.text_content }))
    });
  }, [optimisticMessages]);

  // Add test function to window for debugging
  React.useEffect(() => {
    (window as any).testMessageFlow = () => {
      console.log('🧪 [TEST] Current messages:', sortedMessages);
      console.log('🧪 [TEST] Conversation ID:', conversationId);
      console.log('🧪 [TEST] User:', user);
    };
    
    // Add test function to manually add a message to the query cache
    (window as any).testAddMessage = () => {
      const testMessage = {
        _id: `test-${Date.now()}`,
        conversation_id: conversationId,
        message_type: 'text',
        direction: 'outbound',
        sender_role: 'agent',
        sender_id: user?._id || 'test-user',
        sender_name: user?.first_name || 'Test User',
        text_content: `Test message ${Date.now()}`,
        status: 'sent',
        timestamp: new Date().toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        type: 'text',
      };
      
      console.log('🧪 [TEST] Adding test message:', testMessage);
      
      // Update the query cache directly
      queryClient.setQueryData(
        messageQueryKeys.conversationMessages(conversationId, { limit: 50 }),
        (oldData: any) => {
          if (!oldData) {
            return {
              pages: [{
                messages: [testMessage],
                next_cursor: null,
                has_more: false,
                anchor: 'latest',
                cache_hit: false
              }]
            };
          }
          
          const updatedPages = [...oldData.pages];
          if (updatedPages[0]) {
            updatedPages[0] = {
              ...updatedPages[0],
              messages: [...updatedPages[0].messages, testMessage]
            };
          }
          
          return {
            ...oldData,
            pages: updatedPages
          };
        }
      );
      
      console.log('🧪 [TEST] Test message added to query cache');
    };

    // Add test function to manually trigger optimistic message
    (window as any).testOptimisticMessage = () => {
      console.log('🧪 [TEST] Testing optimistic message flow');
      console.log('🧪 [TEST] Current optimistic messages state:', optimisticMessagesRef.current.size);
      
      const optimisticId = (window as any).addOptimisticMessage?.('Test optimistic message');
      console.log('🧪 [TEST] Optimistic message ID:', optimisticId);
      
      // Check state after adding
      setTimeout(() => {
        console.log('🧪 [TEST] Optimistic messages state after adding:', optimisticMessagesRef.current.size);
        console.log('🧪 [TEST] Optimistic messages:', Array.from(optimisticMessagesRef.current.values()).map(m => ({ id: m._id, text: m.text_content })));
      }, 100);
      
      // Simulate real message after 2 seconds
      setTimeout(() => {
        const realMessage = {
          _id: `real-${Date.now()}`,
          conversation_id: conversationId,
          message_type: 'text',
          direction: 'outbound',
          sender_role: 'agent',
          sender_id: user?._id || 'test-user',
          sender_name: user?.first_name || 'Test User',
          text_content: 'Test optimistic message',
          status: 'sent',
          timestamp: new Date().toISOString(),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          type: 'text',
        };
        
        console.log('🧪 [TEST] Updating optimistic message with real message');
        (window as any).updateOptimisticMessage?.(optimisticId, realMessage);
      }, 2000);
    };

    // Add optimistic message functions to window for external access
    (window as any).addOptimisticMessage = (text: string) => {
      const optimisticMessage = {
        _id: `optimistic-${Date.now()}-${Math.random()}`,
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
      };
      
      console.log('🚀 [OPTIMISTIC] Adding optimistic message:', optimisticMessage._id);
      console.log('🚀 [OPTIMISTIC] Current optimistic messages count:', optimisticMessagesRef.current.size);
      
      // Add to optimistic messages state for immediate rendering
      setOptimisticMessages(prev => {
        const newMap = new Map(prev);
        newMap.set(optimisticMessage._id, optimisticMessage);
        console.log('🚀 [OPTIMISTIC] Updated optimistic messages state, new count:', newMap.size);
        return newMap;
      });
      
      // Also update the query cache for consistency
      queryClient.setQueryData(
        messageQueryKeys.conversationMessages(conversationId, { limit: 50 }),
        (oldData: any) => {
          if (!oldData) {
            return {
              pages: [{
                messages: [optimisticMessage],
                next_cursor: null,
                has_more: false,
                anchor: 'latest',
                cache_hit: false
              }]
            };
          }
          
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
      
      // Force a re-render by updating the previous message IDs tracking
      // This ensures the optimistic message is detected as new
      setTimeout(() => {
        previousMessageIds.current = new Set([...previousMessageIds.current, optimisticMessage._id]);
        console.log('🔄 [OPTIMISTIC] Updated previousMessageIds to include optimistic message');
      }, 0);
      
      // Scroll to bottom immediately for smooth UX
      scrollToBottomSmooth();
      
      return optimisticMessage._id;
    };

    (window as any).updateOptimisticMessage = (optimisticId: string, realMessage: any) => {
      console.log('🔄 [OPTIMISTIC] Updating optimistic message:', optimisticId, 'with real message:', realMessage._id);
      
      // Remove from optimistic messages state
      setOptimisticMessages(prev => {
        const newMap = new Map(prev);
        newMap.delete(optimisticId);
        return newMap;
      });
      
      // Update the query cache
      queryClient.setQueryData(
        messageQueryKeys.conversationMessages(conversationId, { limit: 50 }),
        (oldData: any) => {
          if (!oldData) return oldData;
          
          const updatedPages = oldData.pages.map((page: any) => ({
            ...page,
            messages: page.messages.map((msg: any) => {
              if (msg._id === optimisticId) {
                console.log('✅ [OPTIMISTIC] Replacing optimistic message with real message');
                return { ...realMessage, _id: realMessage._id };
              }
              return msg;
            })
          }));
          
          return {
            ...oldData,
            pages: updatedPages
          };
        }
      );
    };

    (window as any).removeOptimisticMessage = (optimisticId: string) => {
      console.log('🗑️ [OPTIMISTIC] Removing optimistic message:', optimisticId);
      
      // Remove from optimistic messages state
      setOptimisticMessages(prev => {
        const newMap = new Map(prev);
        newMap.delete(optimisticId);
        return newMap;
      });
      
      // Remove from query cache
      queryClient.setQueryData(
        messageQueryKeys.conversationMessages(conversationId, { limit: 50 }),
        (oldData: any) => {
          if (!oldData) return oldData;
          
          const updatedPages = oldData.pages.map((page: any) => ({
            ...page,
            messages: page.messages.filter((msg: any) => msg._id !== optimisticId)
          }));
          
          return {
            ...oldData,
            pages: updatedPages
          };
        }
      );
    };
    
    return () => {
      delete (window as any).testMessageFlow;
      delete (window as any).testAddMessage;
      delete (window as any).testOptimisticMessage;
      delete (window as any).addOptimisticMessage;
      delete (window as any).updateOptimisticMessage;
      delete (window as any).removeOptimisticMessage;
    };
  }, [sortedMessages, conversationId, user, queryClient, scrollToBottomSmooth]);

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
      previousMessageIds.current = new Set(sortedMessages.map(msg => msg._id));
      previousMessageCount.current = sortedMessages.length;
      return;
    }

    // Find truly new messages by comparing IDs
    const currentMessageIds = new Set(sortedMessages.map(msg => msg._id));
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
    const newMessages = sortedMessages.filter(msg => detectedNewMessageIds.has(msg._id));
    const customerMessages = newMessages.filter(msg => msg.direction === 'inbound');
    const agentMessages = newMessages.filter(msg => msg.direction === 'outbound');
    const optimisticMessages = newMessages.filter(msg => msg._id?.startsWith('optimistic-'));

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
    } else if (agentMessages.length > 0 || optimisticMessages.length > 0) {
      // Agent messages or optimistic messages - always scroll to bottom smoothly
      console.log(`📤 [WHATSAPP_UX] ${agentMessages.length} agent messages and ${optimisticMessages.length} optimistic messages, scrolling to bottom`);
      setIsAtBottom(true);
      setShowNewMessagesBanner(false);
      setNewMessagesCount(0);
      setHasShownUnreadMarker(true); // Hide unread marker when agent responds
      scrollToBottomSmooth();
    }

    // Update previous state and track new messages for animation
    previousMessageIds.current = currentMessageIds;
    previousMessageCount.current = sortedMessages.length;
    
    // Add new message IDs to animation tracking (they will be removed after animation completes)
    newMessageIds.current = new Set([...Array.from(newMessageIds.current), ...Array.from(detectedNewMessageIds)]);
    
    // Remove animation tracking after 3 seconds
    setTimeout(() => {
      newMessageIds.current = new Set();
    }, 3000);
  }, [
    sortedMessages, 
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
  if (isLoading && !hasAnyMessages) {
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
  if (!hasAnyMessages) {
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
    isNewMessage?: boolean;
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
    const isNewMessage = newMessageIds.current.has(message._id);
    const isOptimistic = message._id?.startsWith('optimistic-');
    
    if (isOptimistic) {
      console.log('🎯 [RENDER] Rendering optimistic message:', message._id, message.text_content);
    }
    
    items.push({ 
      type: 'message', 
      message, 
      id: message._id || `temp-${index}`,
      isNewMessage: isNewMessage || isOptimistic
    });
  });

  console.log('🎯 [RENDER] Total items to render:', items.length, 'Optimistic messages:', items.filter(item => item.type === 'message' && item.message?._id?.startsWith('optimistic-')).length);

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
                isOptimistic={item.message!._id?.startsWith('optimistic-')}
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
