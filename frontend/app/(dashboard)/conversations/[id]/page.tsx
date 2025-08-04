/**
 * Individual conversation details page with messaging interface.
 * Implements WhatsApp-style chat with real-time messaging.
 */

'use client';

import React, { useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { MessageBubble } from '@/components/chat/MessageBubble';
import { MessageComposer } from '@/components/chat/MessageComposer';
import { ConversationHeader } from '@/components/chat/ConversationHeader';
import { DayBanner } from '@/components/chat/DayBanner';
import { useAuthStore } from '@/lib/store';
import { useMessages, useSendMessage } from '@/features/messages/hooks/useMessages';
import { useConversation } from '@/features/conversations/hooks/useConversations';
import { useConversationWebSocket } from '@/hooks/useWebSocket';
import { SenderType } from '@/features/messages/models/message';
import { isSameDay } from '@/lib/utils';
import { 
  InformationCircleIcon,
  UserIcon
} from '@heroicons/react/24/outline';

export default function ConversationDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuthStore();
  const conversationId = params.id as string;
  
  // Refs for auto-scrolling
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Fetch conversation and messages
  const { 
    data: conversation, 
    isLoading: conversationLoading, 
    error: conversationError 
  } = useConversation(conversationId);
  
  const { 
    data: messagesData, 
    fetchNextPage, 
    hasNextPage, 
    isFetchingNextPage,
    isLoading: messagesLoading,
    error: messagesError 
  } = useMessages(conversationId);

  const sendMessageMutation = useSendMessage();

  // WebSocket connection for real-time messaging
  const { isConnected, sendTypingStart, sendTypingStop } = useConversationWebSocket(conversationId);

  // Scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messagesData?.pages]);

  // Flatten messages from all pages
  const allMessages = messagesData?.pages.flatMap((page) => 
    (page as { messages: unknown[] }).messages
  ) || [];

  // Handle sending a message
  const handleSendMessage = (text: string) => {
    console.log('📤 [SEND] User clicked send message:', text);
    console.log('📤 [SEND] Conversation ID:', conversationId);
    sendMessageMutation.mutate({
      conversation_id: conversationId,
      text_content: text,
    });
  };

  // Handle sending media (placeholder)
  const handleSendMedia = (file: File, caption?: string) => {
    console.log('Send media:', file, caption);
    // TODO: Implement media sending
  };

  // Loading state
  if (conversationLoading || messagesLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <LoadingSpinner size="lg" text="Loading conversation..." />
      </div>
    );
  }

  // Error state
  if (conversationError || messagesError) {
    return (
      <div className="h-full flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="p-6 text-center">
            <InformationCircleIcon className="w-12 h-12 text-error mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Failed to load conversation</h3>
            <p className="text-muted-foreground mb-4">
              {conversationError?.message || messagesError?.message || 'Something went wrong'}
            </p>
            <div className="flex space-x-2 justify-center">
              <Button variant="outline" onClick={() => router.back()}>
                Go Back
              </Button>
              <Button onClick={() => window.location.reload()}>
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Not found state
  if (!conversation) {
    return (
      <div className="h-full flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="p-6 text-center">
            <UserIcon className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Conversation not found</h3>
            <p className="text-muted-foreground mb-4">
              This conversation may have been deleted or you don&apos;t have access to it.
            </p>
            <Button variant="outline" onClick={() => router.push('/conversations')}>
              Back to Conversations
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

      return (
      <div className="h-full flex flex-col bg-background">
        {/* Header */}
        {conversation && (
          <ConversationHeader
            conversation={conversation}
            onBack={() => router.back()}
            onCall={() => console.log('Call customer')}
            onVideoCall={() => console.log('Video call customer')}
            onViewInfo={() => console.log('View customer info')}
            onMoreActions={() => console.log('More actions')}
          />
        )}

      {/* Messages area */}
      <div 
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto p-4 bg-slate-50 dark:bg-slate-800/30"
      >
        {/* Load more messages button */}
        {hasNextPage && (
          <div className="text-center">
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchNextPage()}
              disabled={isFetchingNextPage}
            >
              {isFetchingNextPage ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Loading...
                </>
              ) : (
                'Load older messages'
              )}
            </Button>
          </div>
        )}

        {/* Messages */}
        {allMessages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <UserIcon className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium text-muted-foreground mb-2">
                No messages yet
              </h3>
              <p className="text-muted-foreground">
                Start the conversation by sending a message below.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-1">
            {allMessages.map((message, index) => {
              const previousMessage = index > 0 ? allMessages[index - 1] : null;
              const showDayBanner = !previousMessage || !isSameDay(message.timestamp, previousMessage.timestamp);

              return (
                <React.Fragment key={message._id}>
                  {/* Day banner */}
                  {showDayBanner && (
                    <DayBanner date={message.timestamp} />
                  )}
                  
                  {/* Message bubble */}
                  <MessageBubble
                    message={message}
                    isOwn={message.sender_role === 'agent' && message.sender_id === user?._id}
                    showAvatar={true}
                    showTimestamp={true}
                  />
                </React.Fragment>
              );
            })}
          </div>
        )}

        {/* Scroll anchor */}
        <div ref={messagesEndRef} />
      </div>

      {/* Message composer */}
      <MessageComposer
        onSendMessage={handleSendMessage}
        onSendMedia={handleSendMedia}
        disabled={conversation.status === 'closed'}
        loading={sendMessageMutation.isPending}
        placeholder={
          conversation.status === 'closed' 
            ? "This conversation is closed" 
            : "Type a message..."
        }
        onTypingStart={sendTypingStart}
        onTypingStop={sendTypingStop}
      />
    </div>
  );
}