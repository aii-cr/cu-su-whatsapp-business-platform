/**
 * Virtualized message list component with infinite scroll and bottom anchoring.
 * Implements WhatsApp-style inverted list with proper bottom anchoring.
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Virtuoso, VirtuosoHandle } from 'react-virtuoso';
import { Message } from '../models/message';
import { useMessages } from '../hooks/useMessages';
import { MessageBubble } from '@/features/conversations/components/MessageBubble';
import { DayBanner } from '@/features/conversations/components/DayBanner';
import { LoadingSpinner } from '@/components/feedback/LoadingSpinner';
import { EmptyState } from '@/components/feedback/EmptyState';
import { Button } from '@/components/ui/Button';
import { cn, isSameDay } from '@/lib/utils';

interface VirtualizedMessageListProps {
  conversationId: string;
  className?: string;
}

export function VirtualizedMessageList({ 
  conversationId, 
  className 
}: VirtualizedMessageListProps) {
  const virtuosoRef = useRef<VirtuosoHandle>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [isAtBottom, setIsAtBottom] = useState(true);
  
  const {
    data: messagesData,
    isLoading,
    error,
    hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
    isError,
  } = useMessages(conversationId, 50);

  // Flatten messages from all pages and sort chronologically (oldest to newest)
  const messages = messagesData?.pages.flatMap((page) => page.messages) || [];
  const sortedMessages = [...messages].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  // Handle loading older messages when user scrolls to top
  const handleStartReached = useCallback(async () => {
    if (hasNextPage && !isFetchingNextPage && isInitialized) {
      console.log('🔄 Loading older messages...');
      await fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage, isInitialized]);

  // Initialize scroll position to bottom on first load (no scroll jump)
  useEffect(() => {
    if (!isLoading && sortedMessages.length > 0 && !isInitialized) {
      // Hide the component until positioned, then show immediately at bottom
      setIsInitialized(true);
    }
  }, [isLoading, sortedMessages.length, isInitialized]);

  // Auto-scroll to bottom when new messages arrive (only if user is at bottom)
  const previousMessageCount = useRef(0);
  useEffect(() => {
    if (isInitialized && sortedMessages.length > previousMessageCount.current) {
      if (isAtBottom) {
        // User is at bottom, auto-scroll to new message
        setTimeout(() => {
          virtuosoRef.current?.scrollToIndex({
            index: sortedMessages.length - 1,
            align: 'end',
            behavior: 'auto'
          });
        }, 0);
      }
      previousMessageCount.current = sortedMessages.length;
    }
  }, [sortedMessages.length, isInitialized, isAtBottom]);

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

  // Create items array with day banners
  const items = [];
  sortedMessages.forEach((message, index) => {
    const previousMessage = index > 0 ? sortedMessages[index - 1] : null;
    const showDayBanner = !previousMessage || !isSameDay(message.timestamp, previousMessage.timestamp);
    
    if (showDayBanner) {
      items.push({ type: 'day-banner', date: message.timestamp, id: `day-${message.timestamp}` });
    }
    items.push({ type: 'message', message, id: message._id || `temp-${index}` });
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
                <DayBanner date={item.date} />
              </div>
            );
          }
          
          return (
            <div className="px-4 py-1">
              <MessageBubble
                key={item.id}
                message={item.message}
                isOwn={item.message.direction === 'outbound'}
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
    </div>
  );
}
