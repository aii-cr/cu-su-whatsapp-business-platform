import React, { useEffect, useRef } from 'react';
import { Message } from '../models/message';
import { useMessageInfiniteScroll } from '../hooks/useMessageInfiniteScroll';
import { Button } from '@/components/ui/Button';
import { MessageBubble } from '@/components/chat/MessageBubble';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { EmptyState } from '@/components/feedback/EmptyState';

interface MessageListProps {
  conversationId: string;
}

export function MessageList({ conversationId }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const {
    messages,
    isLoading,
    error,
    hasNextPage,
    isFetchingNextPage,
    handleLoadOlderMessages,
    messagesContainerRef,
    scrollToBottom,
    isNearBottom,
  } = useMessageInfiniteScroll({ conversationId });

  // Sort messages chronologically (oldest → newest)
  const sortedMessages = [...messages].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  // Auto-scroll to bottom when new messages arrive (but only if user is near bottom)
  useEffect(() => {
    const timer = setTimeout(() => {
      if (isNearBottom() || messages.length === 1) {
        scrollToBottom();
      }
    }, 100);

    return () => clearTimeout(timer);
  }, [messages.length, scrollToBottom, isNearBottom]);

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
            <Button onClick={() => window.location.reload()} variant="primary">
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
              onClick={handleLoadOlderMessages}
              disabled={isFetchingNextPage}
              variant="secondary"
              size="sm"
              className="text-sm"
            >
              {isFetchingNextPage ? (
                <>
                  <LoadingSpinner size="xs" className="mr-2" />
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
