/**
 * Individual conversation details page with messaging interface.
 * Implements WhatsApp-style chat with real-time messaging.
 */

'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/feedback/LoadingSpinner';
import { MessageBubble } from '@/features/conversations/components/MessageBubble';
import { MessageComposer } from '@/features/conversations/components/MessageComposer';
import { ConversationHeader } from '@/features/conversations/components/ConversationHeader';
import { DayBanner } from '@/features/conversations/components/DayBanner';
import { UnreadMessagesBanner } from '@/features/conversations/components/UnreadMessagesBanner';

import { useAuthStore } from '@/lib/store';
import { useSendMessage } from '@/features/messages/hooks/useMessages';
import { useConversationWithMessages, conversationQueryKeys } from '@/features/conversations/hooks/useConversations';
import { useConversationWebSocket } from '@/hooks/useWebSocket';
import { useUnreadMessages } from '@/features/conversations/hooks/useUnreadMessages';
import { useQueryClient } from '@tanstack/react-query';
import { Message } from '@/features/messages/models/message';
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
  const unreadMessagesRef = useRef<HTMLDivElement>(null);
  const [shouldScrollToBottom, setShouldScrollToBottom] = useState(true);

  // WebSocket connection for real-time messaging
  const webSocket = useConversationWebSocket(conversationId);
  const { isConnected, sendTypingStart, sendTypingStop } = webSocket;

  // Fetch conversation with messages and initial unread count
  const { 
    data: conversationWithMessages, 
    isLoading: conversationLoading, 
    error: conversationError 
  } = useConversationWithMessages(conversationId, 50, 0);

  // Extract data from the combined response
  const conversation = conversationWithMessages?.conversation;
  const initialUnreadCount = conversationWithMessages?.initial_unread_count || 0;
  const messagesData = conversationWithMessages ? {
    pages: [{ messages: conversationWithMessages.messages }],
    pageParams: [0]
  } : undefined;
  const messagesLoading = conversationLoading;
  const messagesError = conversationError;
  const hasNextPage = conversationWithMessages?.has_more_messages || false;
  const isFetchingNextPage = false; // Not implemented for this endpoint yet
  const fetchNextPage = () => {}; // Not implemented for this endpoint yet

  // Get all messages for rendering
  const allMessages = messagesData?.pages?.[0]?.messages || [];

  // Unread messages management with initial count from backend
  const {
    unreadCount,
    bannerUnreadCount, // Separate count for banner display
    isVisible: isUnreadBannerVisible,
    hasMarkedAsRead,
    hasRepliedToUnread,
    isCurrentlyViewing,
    markMessagesAsRead
  } = useUnreadMessages({
    conversationId,
    autoMarkAsRead: true,
    enabled: !!conversationId,
    wsClient: webSocket.client,
    isConnected: isConnected,
    initialUnreadCount: initialUnreadCount
  });

  const sendMessageMutation = useSendMessage();
  const queryClient = useQueryClient();

  // Handle optimistic updates for the new query structure
  const handleSendMessage = (text: string) => {
    console.log('📤 [SEND] User clicked send message:', text);
    console.log('📤 [SEND] Conversation ID:', conversationId);
    
    // Create optimistic message
    const optimisticMessage = {
      _id: `optimistic-${Date.now()}`,
      conversation_id: conversationId,
      message_type: 'text',
      direction: 'outbound',
      sender_role: 'agent',
      sender_id: user?._id || '',
      sender_name: user?.name || user?.email || 'You',
      text_content: text,
      status: 'sending',
      timestamp: new Date().toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      type: 'text',
      isOptimistic: true,
    };

    // Add optimistic message to the conversation with messages query
    queryClient.setQueryData(
      [...conversationQueryKeys.detail(conversationId), 'with-messages', 50, 0],
      (old: unknown) => {
        if (!old || typeof old !== 'object') return old;
        const oldData = old as { messages: Message[]; messages_total: number };
        return {
          ...oldData,
          messages: [...oldData.messages, optimisticMessage],
          messages_total: oldData.messages_total + 1,
        };
      }
    );

    // Send the actual message
    sendMessageMutation.mutate({
      conversation_id: conversationId,
      text_content: text,
    }, {
      onSuccess: (response) => {
        // Update optimistic message with real data
        queryClient.setQueryData(
          [...conversationQueryKeys.detail(conversationId), 'with-messages', 50, 0],
          (old: unknown) => {
            if (!old || typeof old !== 'object') return old;
            const oldData = old as { messages: Message[] };
            const sentMessage = response.message;
            
            // Replace optimistic message with real data
            const updatedMessages = oldData.messages.map((msg: Message) => 
              (msg as Message & { isOptimistic?: boolean }).isOptimistic ? { ...sentMessage, status: 'sent' } : msg
            );
            
            return {
              ...oldData,
              messages: updatedMessages,
            };
          }
        );

        // Trigger banner to disappear by setting hasRepliedToUnread
        // This will be handled by the WebSocket message handler
        console.log('✅ [SEND] Message sent successfully, banner should disappear');
      }
    });
  };

  // Scroll to bottom when new messages arrive
  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior });
    }
  }, []);

  // Scroll to unread messages
  const scrollToUnread = useCallback(() => {
    if (unreadMessagesRef.current) {
      unreadMessagesRef.current.scrollIntoView({ behavior: 'smooth' });
    } else {
      // If no unread marker, scroll to bottom
      scrollToBottom();
    }
  }, [scrollToBottom]);



  // Check if user is near bottom of messages
  const isNearBottom = useCallback(() => {
    const container = messagesContainerRef.current;
    if (!container) return true;
    const threshold = 150; // Increased threshold for better UX
    return container.scrollHeight - container.scrollTop - container.clientHeight < threshold;
  }, []);

  // Handle scroll events to determine if we should auto-scroll
  const handleScroll = useCallback(() => {
    const nearBottom = isNearBottom();
    setShouldScrollToBottom(nearBottom);
  }, [isNearBottom]);

  // Auto-scroll when messages load or new messages arrive
  useEffect(() => {
    if (messagesData?.pages && messagesData.pages.length > 0) {
      const timer = setTimeout(() => {
        // Always scroll to bottom on initial load
        if (messagesData.pages[0].messages.length === 1 || shouldScrollToBottom) {
          scrollToBottom('smooth');
        }
      }, 100);

      return () => clearTimeout(timer);
    }
  }, [messagesData?.pages, shouldScrollToBottom, scrollToBottom]);

  // Auto-scroll to bottom when new messages arrive (if user is near bottom)
  useEffect(() => {
    if (messagesData?.pages && messagesData.pages.length > 0) {
      const currentMessages = messagesData.pages.flatMap((page) => 
        (page as { messages: Message[] }).messages
      );
      
      // Check if there are new messages (more than before)
      if (currentMessages.length > 0 && shouldScrollToBottom) {
        const timer = setTimeout(() => {
          scrollToBottom('smooth');
        }, 50);

        return () => clearTimeout(timer);
      }
    }
  }, [messagesData?.pages, shouldScrollToBottom, scrollToBottom]);



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



      {/* Debug button - remove this after testing */}
      {process.env.NODE_ENV === 'development' && (
        <div className="p-2 bg-yellow-100 dark:bg-yellow-900 border-b">
          <button
            onClick={() => {
              console.log('🔧 [DEBUG] Manual mark as read triggered');
              markMessagesAsRead();
            }}
            className="px-3 py-1 bg-blue-500 text-white rounded text-sm"
          >
            🔧 Debug: Mark as Read
          </button>
          <button
            onClick={() => {
              console.log('🔧 [DEBUG] Direct WebSocket test');
              console.log('WebSocket client:', webSocket.client);
              console.log('WebSocket connected:', webSocket.client?.isConnected);
              if (webSocket.client?.isConnected) {
                webSocket.client.markMessagesAsRead(conversationId);
                console.log('✅ Direct WebSocket message sent');
              } else {
                console.log('❌ WebSocket not connected');
              }
            }}
            className="px-3 py-1 bg-green-500 text-white rounded text-sm ml-2"
          >
            🔧 Direct WS Test
          </button>
          <span className="ml-2 text-sm">
            DB Unread: {unreadCount} | Banner Unread: {bannerUnreadCount} | Banner: {isUnreadBannerVisible ? 'Visible' : 'Hidden'} | Replied: {hasRepliedToUnread ? 'Yes' : 'No'} | Marked: {hasMarkedAsRead ? 'Yes' : 'No'} | WS: {isConnected ? 'Connected' : 'Disconnected'} | Viewing: {isCurrentlyViewing ? 'Yes' : 'No'}
          </span>
        </div>
      )}

      {/* Messages area */}
      <div 
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto p-4 bg-slate-50 dark:bg-slate-800/30"
        onScroll={handleScroll}
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
              
              // Check if this is the first unread message
              const isFirstUnread = message.direction === 'inbound' && 
                                   message.status !== 'read' && 
                                   !allMessages.slice(0, index).some(m => 
                                     m.direction === 'inbound' && m.status !== 'read'
                                   );

              return (
                <React.Fragment key={message._id}>
                  {/* Day banner */}
                  {showDayBanner && (
                    <DayBanner date={message.timestamp} />
                  )}
                  
                  {/* Unread Messages Banner - positioned right above first unread message */}
                  {isFirstUnread && isUnreadBannerVisible && (
                    <div ref={unreadMessagesRef}>
                      <UnreadMessagesBanner
                        unreadCount={bannerUnreadCount}
                        onScrollToUnread={scrollToUnread}
                        isVisible={true}
                      />
                    </div>
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