/**
 * Conversation Header with AI Context integration
 * Wraps the ConversationHeader component with AI context functionality
 */

'use client';

import React from 'react';
import { ConversationHeader, ConversationHeaderProps } from './ConversationHeader';
import { useAIContext } from '../context/AIContextProvider';

export const ConversationHeaderWithAI: React.FC<ConversationHeaderProps> = (props) => {
  const { openModal } = useAIContext();

  return (
    <ConversationHeader
      {...props}
      onAIContext={openModal}
    />
  );
};
