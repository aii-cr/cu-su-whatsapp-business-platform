/**
 * Message list component with infinite scroll and load older messages functionality.
 * Displays messages in descending order (newest first) and allows loading older messages.
 */

import React, { useEffect, useRef } from 'react';
import { Message } from '../models/message';
import { useMessageInfiniteScroll } from '../hooks/useMessageInfiniteScroll';
import { Button } from '@/components/ui/Button';
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

  // Auto-scroll to bottom when new messages arrive (but only if user is near bottom)
  useEffect(() => {
    // Always scroll to bottom when messages change (for new messages)
    // We do this with a small delay to ensure DOM has updated
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
          {/* Display messages in chronological order (oldest to newest) - WhatsApp style */}
          {[...messages].reverse().map((message, index) => (
            <MessageBubble
              key={message._id || `temp-${index}`}
              message={message}
              isFromCurrentUser={message.direction === 'outbound'}
            />
          ))}
        </div>
        
        {/* This div ensures we can scroll to the bottom */}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}

// Placeholder MessageBubble component - you can replace this with your existing one
interface MessageBubbleProps {
  message: Message;
  isFromCurrentUser: boolean;
}

function MessageBubble({ message, isFromCurrentUser }: MessageBubbleProps) {
  const isOptimistic = (message as any).isOptimistic;
  const isPending = message.status === 'pending';
  const isSending = message.status === 'sending';
  
  const getStatusIcon = () => {
    if (isOptimistic || isPending || isSending) {
      return <LoadingSpinner size="xs" className="ml-1" />;
    }
    
    switch (message.status) {
      case 'sent':
        return <span className="text-blue-500">✓</span>;
      case 'delivered':
        return <span className="text-green-500">✓✓</span>;
      case 'read':
        return <span className="text-green-600">✓✓</span>;
      default:
        return <span className="text-muted-foreground">⏱️</span>;
    }
  };

  const getTimestamp = () => {
    if (isOptimistic || isPending) {
      return 'Sending...';
    }
    
    return new Date(message.timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className={`flex ${isFromCurrentUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div
        className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
          isFromCurrentUser
            ? 'bg-primary text-primary-foreground'
            : 'bg-surface text-foreground border border-border'
        } ${(isOptimistic || isPending) ? 'opacity-80' : ''}`}
      >
        <p className="text-sm leading-relaxed">{message.text_content}</p>
        <div className="flex items-center justify-between mt-2">
          <span className="text-xs opacity-70">
            {getTimestamp()}
          </span>
          {isFromCurrentUser && (
            <div className="flex items-center text-xs ml-2">
              {getStatusIcon()}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}