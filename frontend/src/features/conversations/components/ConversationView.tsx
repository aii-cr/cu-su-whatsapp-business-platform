/**
 * Conversation view component that displays messages and handles message sending.
 * Demonstrates the fixed message pagination and optimistic UI functionality.
 */

import React from 'react';
import { MessageList } from '@/features/messages/components/MessageList';
import { MessageComposer } from '@/features/conversations/components/MessageComposer';

interface ConversationViewProps {
  conversationId: string;
}

export function ConversationView({ conversationId }: ConversationViewProps) {
  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <div className="border-b border-border px-4 py-3">
        <h2 className="text-lg font-semibold text-foreground">
          Conversation
        </h2>
      </div>

      {/* Message List - Now with fixed pagination and optimistic UI */}
      <MessageList conversationId={conversationId} />

      {/* Message Composer */}
      <div className="border-t border-border p-4">
        <MessageComposer conversationId={conversationId} />
      </div>
    </div>
  );
}

// Placeholder MessageComposer component
interface MessageComposerProps {
  conversationId: string;
}

function MessageComposer({ conversationId }: MessageComposerProps) {
  const [message, setMessage] = React.useState('');

  const handleSend = () => {
    if (message.trim()) {
      // This would use the useSendMessage hook
      console.log('Sending message:', message, 'to conversation:', conversationId);
      setMessage('');
    }
  };

  return (
    <div className="flex space-x-2">
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && handleSend()}
        placeholder="Type a message..."
        className="flex-1 px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
      />
      <button
        onClick={handleSend}
        disabled={!message.trim()}
        className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-secondary disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Send
      </button>
    </div>
  );
}