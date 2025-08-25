/**
 * AI Typing Indicator Component
 * Shows when AI assistant is processing a message with real-time activity updates
 */

import React, { useState, useEffect } from 'react';
import styles from './AITypingIndicator.module.scss';

interface AITypingIndicatorProps {
  conversationId: string;
  className?: string;
}

interface AIActivity {
  activityType: string;
  activityDescription: string;
  timestamp: string;
}

export function AITypingIndicator({ conversationId, className = '' }: AITypingIndicatorProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [currentActivity, setCurrentActivity] = useState<AIActivity | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);

  useEffect(() => {
    const handleAIProcessingStarted = (event: CustomEvent) => {
      const { conversationId: eventConversationId } = event.detail;
      if (eventConversationId === conversationId) {
        console.log('🤖 [AI_INDICATOR] AI processing started for conversation:', conversationId);
        setIsVisible(true);
        setCurrentActivity(null);
      }
    };

    const handleAIAgentActivity = (event: CustomEvent) => {
      const { 
        conversationId: eventConversationId, 
        activityType, 
        activityDescription, 
        timestamp 
      } = event.detail;
      
      if (eventConversationId === conversationId && isVisible) {
        console.log('🤖 [AI_INDICATOR] AI activity update:', activityType, activityDescription);
        
        // Show updating animation briefly
        setIsUpdating(true);
        setTimeout(() => setIsUpdating(false), 200);
        
        setCurrentActivity({
          activityType,
          activityDescription,
          timestamp
        });
      }
    };

    const handleAIProcessingCompleted = (event: CustomEvent) => {
      const { conversationId: eventConversationId } = event.detail;
      if (eventConversationId === conversationId) {
        console.log('🤖 [AI_INDICATOR] AI processing completed for conversation:', conversationId);
        
        // Hide with a slight delay to allow for smooth transition
        setTimeout(() => {
          setIsVisible(false);
          setCurrentActivity(null);
        }, 500);
      }
    };

    // Add event listeners
    window.addEventListener('ai-processing-started', handleAIProcessingStarted as EventListener);
    window.addEventListener('ai-agent-activity', handleAIAgentActivity as EventListener);
    window.addEventListener('ai-processing-completed', handleAIProcessingCompleted as EventListener);

    // Cleanup
    return () => {
      window.removeEventListener('ai-processing-started', handleAIProcessingStarted as EventListener);
      window.removeEventListener('ai-agent-activity', handleAIAgentActivity as EventListener);
      window.removeEventListener('ai-processing-completed', handleAIProcessingCompleted as EventListener);
    };
  }, [conversationId, isVisible]);

  if (!isVisible) {
    console.log('🤖 [AI_INDICATOR] Component not visible, returning null');
    return null;
  }

  console.log('🤖 [AI_INDICATOR] Rendering AI typing indicator with activity:', currentActivity?.activityDescription);

  const getActivityDescription = () => {
    if (!currentActivity) {
      return 'Starting up...';
    }

    // Map activity types to user-friendly descriptions
    switch (currentActivity.activityType) {
      case 'intent_detection':
        return 'Analyzing message intent';
      case 'rag_search':
        return 'Using internal knowledge';
      case 'response_generation':
        return 'Generating response';
      case 'tool_execution':
        return 'Processing request';
      default:
        return currentActivity.activityDescription || 'Processing...';
    }
  };

  return (
    <div className={`${styles.aiTypingIndicator} ${className}`} role="status" aria-live="polite">
      <div className={styles.avatar} aria-hidden="true" />
      
      <div className={styles.content}>
        <div className={styles.mainText}>
          <span>AI Assistant is writing</span>
          <div className={styles.dots} aria-hidden="true">
            <div className={styles.dot} />
            <div className={styles.dot} />
            <div className={styles.dot} />
          </div>
        </div>
        
        <div className={`${styles.activityText} ${isUpdating ? styles.updating : ''}`}>
          <div className={styles.activityIcon} aria-hidden="true" />
          <span>{getActivityDescription()}</span>
        </div>
      </div>
    </div>
  );
}

export default AITypingIndicator;
