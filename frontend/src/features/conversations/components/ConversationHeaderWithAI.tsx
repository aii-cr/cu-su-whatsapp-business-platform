/**
 * Conversation Header with AI Context and Summarization integration
 * Wraps the ConversationHeader component with AI context and summarization functionality
 */

'use client';

import React, { useState } from 'react';
import { ConversationHeader, ConversationHeaderProps } from './ConversationHeader';
import { ConversationSummaryModal } from './ConversationSummaryModal';
import { useAIContext } from '../context/AIContextProvider';

export const ConversationHeaderWithAI: React.FC<ConversationHeaderProps> = (props) => {
  const { openModal } = useAIContext();
  const [showSummaryModal, setShowSummaryModal] = useState(false);

  const handleSummarize = () => {
    setShowSummaryModal(true);
  };

  return (
    <>
      <ConversationHeader
        {...props}
        onAIContext={openModal}
        onSummarize={handleSummarize}
      />
      
      <ConversationSummaryModal
        open={showSummaryModal}
        onOpenChange={setShowSummaryModal}
        conversationId={props.conversation._id}
        conversationTitle={props.conversation.customer_name || props.conversation.customer_phone}
        conversation={props.conversation}
      />
    </>
  );
};
