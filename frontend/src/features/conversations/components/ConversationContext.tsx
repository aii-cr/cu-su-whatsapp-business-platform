/**
 * Conversation Context Component
 * Displays AI conversation memory and context information
 */

'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/feedback/LoadingSpinner';
import { useConversationContext } from '@/features/ai/hooks/useConversationContext';
import { 
  CpuChipIcon, 
  ClockIcon, 
  ChatBubbleLeftRightIcon,
  TrashIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import styles from './ConversationContext.module.scss';

interface ConversationContextProps {
  conversationId: string;
  className?: string;
  variant?: 'sidebar' | 'modal';
}

export const ConversationContext: React.FC<ConversationContextProps> = ({
  conversationId,
  className = '',
  variant = 'sidebar'
}) => {
  const { context, loading, error, refreshContext, clearMemory, isClearing } = useConversationContext(conversationId);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleClearMemory = async () => {
    if (!confirm('Are you sure you want to clear the AI memory for this conversation? This will reset the conversation context.')) {
      return;
    }
    
    await clearMemory();
  };

  if (loading && !context) {
    return (
      <div className={`${styles.contextContainer} ${className}`}>
        <div className={styles.loadingContainer}>
          <LoadingSpinner size="sm" text="Loading context..." />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${styles.contextContainer} ${className}`}>
        <div className={styles.errorContainer}>
          <div className={styles.errorContent}>
            <InformationCircleIcon className={styles.errorIcon} />
            <span className={styles.errorText}>{error}</span>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={refreshContext}
              className={styles.retryButton}
            >
              Retry
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!context) {
    return null;
  }

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleTimeString();
    } catch {
      return 'Unknown';
    }
  };

  const getIntentFromContent = (content: string): string => {
    const lowerContent = content.toLowerCase();
    if (lowerContent.includes('reserva') || lowerContent.includes('booking')) return 'booking';
    if (lowerContent.includes('pago') || lowerContent.includes('payment')) return 'payment';
    if (lowerContent.includes('precio') || lowerContent.includes('price')) return 'pricing';
    if (lowerContent.includes('horario') || lowerContent.includes('schedule')) return 'scheduling';
    return 'general';
  };

  return (
    <div className={`${styles.contextContainer} ${className}`} data-variant={variant}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerContent}>
          <div className={styles.titleSection}>
            <CpuChipIcon className={styles.titleIcon} />
            <h3 className={styles.title}>AI Context</h3>
            <Badge variant="outline" className={styles.messageCount}>
              {context.memory_size} messages
            </Badge>
          </div>
          <div className={styles.headerActions}>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className={styles.expandButton}
            >
              {isExpanded ? 'Collapse' : 'Expand'}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleClearMemory}
              disabled={isClearing}
              className={styles.clearButton}
              title="Clear AI memory"
            >
              <TrashIcon className={styles.clearIcon} />
            </Button>
          </div>
        </div>
      </div>
      
      {/* Content */}
      <div className={styles.content}>
        {/* Summary */}
        {context.summary && (
          <div className={styles.section}>
            <div className={styles.sectionHeader}>
              <ChatBubbleLeftRightIcon className={styles.sectionIcon} />
              <span className={styles.sectionTitle}>Conversation Summary</span>
            </div>
            <div className={styles.summaryContent}>
              {context.summary}
            </div>
          </div>
        )}

        {/* Last Activity */}
        {context.last_activity && (
          <div className={styles.lastActivity}>
            <ClockIcon className={styles.activityIcon} />
            <span className={styles.activityText}>
              Last activity: {formatTimestamp(context.last_activity)}
            </span>
          </div>
        )}

        {/* Session Data */}
        {Object.keys(context.session_data).length > 0 && (
          <div className={styles.section}>
            <div className={styles.sectionTitle}>Session Data</div>
            <div className={styles.sessionData}>
              {Object.entries(context.session_data).map(([key, value]) => (
                <div key={key} className={styles.sessionItem}>
                  <span className={styles.sessionKey}>{key}:</span>
                  <span className={styles.sessionValue}>{String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Conversation History (Expandable) */}
        {isExpanded && context.history.length > 0 && (
          <div className={styles.section}>
            <div className={styles.sectionTitle}>Recent History</div>
            <div className={styles.historyContainer}>
              {context.history.slice(-6).map((message, index) => (
                <div 
                  key={`${message.message_id}-${index}`}
                  className={`${styles.historyItem} ${
                    message.role === 'user' 
                      ? styles.userMessage 
                      : styles.aiMessage
                  }`}
                >
                  <div className={styles.messageHeader}>
                    <Badge 
                      variant={message.role === 'user' ? 'default' : 'secondary'}
                      className={styles.roleBadge}
                    >
                      {message.role === 'user' ? 'User' : 'AI'}
                    </Badge>
                    <span className={styles.messageTime}>
                      {formatTimestamp(message.timestamp)}
                    </span>
                  </div>
                  <p className={styles.messageContent}>
                    {message.content}
                  </p>
                  {message.role === 'user' && (
                    <div className={styles.intentBadge}>
                      <Badge 
                        variant="outline" 
                        className={styles.intentBadgeContent}
                      >
                        {getIntentFromContent(message.content)}
                      </Badge>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {context.history.length === 0 && (
          <div className={styles.emptyState}>
            <ChatBubbleLeftRightIcon className={styles.emptyIcon} />
            <p className={styles.emptyText}>No conversation history yet</p>
          </div>
        )}
      </div>
    </div>
  );
};
