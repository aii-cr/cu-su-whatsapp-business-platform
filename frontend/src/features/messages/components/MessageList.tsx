import React from 'react';
import { VirtualizedMessageList } from './VirtualizedMessageList';

interface MessageListProps {
  conversationId: string;
  className?: string;
}

export function MessageList({ conversationId, className }: MessageListProps) {
  return (
    <VirtualizedMessageList 
      conversationId={conversationId} 
      className={className}
    />
  );
}
