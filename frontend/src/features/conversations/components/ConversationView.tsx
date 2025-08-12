/**
 * Conversation view component that displays messages and handles message sending.
 * Demonstrates the fixed message pagination and optimistic UI functionality.
 */

import React from 'react';
import { MessageList } from '@/features/messages/components/MessageList';
import { MessageComposer } from '@/features/conversations/components/MessageComposer';
import { useSendMessage } from '@/features/messages/hooks/useMessages';
import { ConversationTagManager } from '@/features/tags';

interface ConversationViewProps {
  conversationId: string;
}

export function ConversationView({ conversationId }: ConversationViewProps) {
  const sendMessageMutation = useSendMessage();

  const handleSendMessage = (text: string) => {
    sendMessageMutation.mutate({
      conversation_id: conversationId,
      text_content: text,
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
        <h2 className="text-lg font-semibold text-foreground">
          Conversation
        </h2>
        
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