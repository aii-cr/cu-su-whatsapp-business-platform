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
import { VirtualizedMessageList } from '@/features/messages/components/VirtualizedMessageList';

import { useAuthStore } from '@/lib/store';
import { useSendMessage } from '@/features/messages/hooks/useMessages';
import { useConversation, conversationQueryKeys } from '@/features/conversations/hooks/useConversations';
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
  
  // State for unread message tracking
  const unreadMessagesRef = useRef<HTMLDivElement>(null);

  // WebSocket connection for real-time messaging
  const webSocket = useConversationWebSocket(conversationId);
  const { isConnected, sendTypingStart, sendTypingStop } = webSocket;

  // Fetch conversation data only (messages handled by VirtualizedMessageList)
  const { 
    data: conversation, 
    isLoading: conversationLoading, 
    error: conversationError 
  } = useConversation(conversationId);

  // Unread messages management with initial count from backend
  const {
    unreadCount,
    bannerUnreadCount, // Separate count for banner display
    isVisible: isUnreadBannerVisible,
    hasMarkedAsRead,
    hasRepliedToUnread,
    isCurrentlyViewing,
    markMessagesAsRead,
    hideBanner
  } = useUnreadMessages({
    conversationId,
    autoMarkAsRead: true,
    enabled: !!conversationId,
    wsClient: webSocket.client,
    isConnected: isConnected,
    initialUnreadCount: 0
  });

  const sendMessageMutation = useSendMessage();
  const queryClient = useQueryClient();

  // Handle sending messages with optimistic updates
  const handleSendMessage = (text: string) => {
    console.log('📤 [SEND] User clicked send message:', text);
    console.log('📤 [SEND] Conversation ID:', conversationId);
    
    // Add optimistic message immediately
    const optimisticId = (window as any).addOptimisticMessage?.(text);
    console.log('🚀 [SEND] Added optimistic message with ID:', optimisticId);
    
    // Send the actual message
    sendMessageMutation.mutate({
      conversation_id: conversationId,
      text_content: text,
    }, {
      onSuccess: (response) => {
        console.log('✅ [SEND] Message sent successfully:', response);
        
        // Update optimistic message with real data
        if (optimisticId && response) {
          (window as any).updateOptimisticMessage?.(optimisticId, response);
        }
        
        // Hide banner for immediate feedback and mark as replied
        hideBanner();
        // Mark that we've replied to unread messages
        if (hasRepliedToUnread === false) {
          // This will be handled by the useUnreadMessages hook
          console.log('✅ [SEND] Agent replied to unread messages');
        }
      },
      onError: (error) => {
        console.error('❌ [SEND] Failed to send message:', error);
        
        // Remove optimistic message on error
        if (optimisticId) {
          (window as any).removeOptimisticMessage?.(optimisticId);
        }
      }
    });
  };

  // Media sending handler
  const handleSendMedia = (file: File, caption?: string) => {
    console.log('Send media:', file, caption);
    // TODO: Implement media sending
  };


  // Loading state
  if (conversationLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <LoadingSpinner size="lg" text="Loading conversation..." />
      </div>
    );
  }

  // Error state
  if (conversationError) {
    return (
      <div className="h-full flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="p-6 text-center">
            <InformationCircleIcon className="w-12 h-12 text-error mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Failed to load conversation</h3>
            <p className="text-muted-foreground mb-4">
              {conversationError?.message || 'Something went wrong'}
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

      {/* Messages area with virtualized infinite scroll */}
      <VirtualizedMessageList 
        conversationId={conversationId}
        className="flex-1"
      />

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