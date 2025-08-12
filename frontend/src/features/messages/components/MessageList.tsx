import React, { useEffect, useRef } from 'react';
import { Message } from '../models/message';
import { useMessages } from '../hooks/useMessages';
import { Button } from '@/components/ui/Button';
import { MessageBubble } from '@/features/conversations/components/MessageBubble';
import { LoadingSpinner } from '@/components/feedback/LoadingSpinner';
import { EmptyState } from '@/components/feedback/EmptyState';

interface MessageListProps {
  conversationId: string;
}

export function MessageList({ conversationId }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  
  const {
    data: messagesData,
    isLoading,
    error,
    hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
  } = useMessages(conversationId);

  // Flatten messages from all pages and sort chronologically (oldest → newest)
  const messages = messagesData?.pages.flatMap((page) => page.messages) || [];
  const sortedMessages = [...messages].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  // Scroll utility functions
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const isNearBottom = () => {
    const container = messagesContainerRef.current;
    if (!container) return true;
    const threshold = 100; // pixels from bottom
    return container.scrollHeight - container.scrollTop - container.clientHeight < threshold;
  };

  // Auto-scroll to bottom when new messages arrive (but only if user is near bottom)
  useEffect(() => {
    const timer = setTimeout(() => {
      if (isNearBottom() || messages.length === 1) {
        scrollToBottom();
      }
    }, 100);

    return () => clearTimeout(timer);
  }, [messages.length]);

  if (isLoading && (!messages || messages.length === 0)) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <LoadingSpinner size="md" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center">
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

  if (!messages || messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <EmptyState
          title="No messages yet"
          description="Start the conversation by sending your first message."
        />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto px-4 py-2"
      >
        {/* Load older messages button at the top */}
        {hasNextPage && (
          <div className="flex justify-center py-4 mb-4">
            <Button
              onClick={() => fetchNextPage()}
              disabled={isFetchingNextPage}
              variant="secondary"
              size="sm"
              className="text-sm"
            >
              {isFetchingNextPage ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Loading older messages...
                </>
              ) : (
                'Load older messages'
              )}
            </Button>
          </div>
        )}

        <div className="space-y-2">
          {sortedMessages.map((message, index) => (
            <MessageBubble
              key={message._id || `temp-${index}`}
              message={message}
              isOwn={message.direction === 'outbound'}
            />
          ))}
        </div>

        {/* This div ensures we can scroll to the bottom */}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
