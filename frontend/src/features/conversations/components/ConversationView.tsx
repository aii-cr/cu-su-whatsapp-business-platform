/**
 * Conversation view component that displays messages and handles message sending.
 * Demonstrates the fixed message pagination and optimistic UI functionality.
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { MessageList } from '@/features/messages/components/MessageList';
import { MessageComposer } from '@/features/conversations/components/MessageComposer';
import { AutoReplyToggle } from '@/features/conversations/components/AutoReplyToggle';
import { useSendMessage } from '@/features/messages/hooks/useMessages';
import { ConversationTagManager } from '@/features/tags';
import { ConversationsApi } from '../api/conversationsApi';

interface ConversationViewProps {
  conversationId: string;
}

export function ConversationView({ conversationId }: ConversationViewProps) {
  const sendMessageMutation = useSendMessage();
  
  // Fetch conversation data to get AI auto-reply state
  const { data: conversation } = useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: () => ConversationsApi.getConversation(conversationId),
    enabled: !!conversationId,
  });

  const handleSendMessage = (text: string) => {
    console.log('🚀 [CONVERSATION] Sending message:', text);
    console.log('🚀 [CONVERSATION] Conversation ID:', conversationId);
    
    sendMessageMutation.mutate({
      conversation_id: conversationId,
      text_content: text,
    }, {
      onSuccess: (data) => {
        console.log('✅ [CONVERSATION] Message sent successfully:', data);
      },
      onError: (error) => {
        console.error('❌ [CONVERSATION] Message send failed:', error);
      }
    });
  };

  const handleSendMedia = (file: File, caption?: string) => {
    console.log('Send media:', file, caption);
    // TODO: Implement media sending
  };

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <div className="border-b border-border px-4 py-3 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-foreground">
            Conversation
          </h2>
          
          {/* AI Auto-Reply Toggle */}
          <AutoReplyToggle 
            conversationId={conversationId}
            initialEnabled={conversation?.ai_autoreply_enabled ?? true}
            currentEnabled={conversation?.ai_autoreply_enabled ?? true}
            className="ml-auto"
          />
        </div>
        
        {/* Tags Manager */}
        <ConversationTagManager 
          conversationId={conversationId}
          variant="default"
          size="md"
          showAddButton={true}
        />
      </div>

      {/* Message List - Now with fixed pagination and optimistic UI */}
      <MessageList conversationId={conversationId} />

      {/* Message Composer */}
      <MessageComposer
        onSendMessage={handleSendMessage}
        onSendMedia={handleSendMedia}
        loading={sendMessageMutation.isPending}
        placeholder="Type a message..."
      />
    </div>
  );
}