/**
 * Modal component for displaying conversation summaries.
 * Supports markdown rendering and provides summary generation controls.
 */

import * as React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/Dialog';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { 
  DocumentTextIcon, 
  ClockIcon, 
  ChatBubbleLeftRightIcon,
  SparklesIcon,
  ArrowPathIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { useConversationSummarizer } from '../hooks/useConversationSummarizer';
import { ConversationSummaryResponse } from '../api/summarizerApi';
import { formatRelativeTime } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import styles from './ConversationSummaryModal.module.scss';

export interface ConversationSummaryModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  conversationId: string;
  conversationTitle?: string;
}

export function ConversationSummaryModal({
  open,
  onOpenChange,
  conversationId,
  conversationTitle = 'Conversation'
}: ConversationSummaryModalProps) {
  const {
    isLoading,
    isGenerating,
    summary,
    error,
    generateSummary,
    refreshSummary,
    clearSummary,
    processingTime,
    lastGenerated
  } = useConversationSummarizer({
    conversationId,
    summaryType: 'general',
    includeMetadata: true
  });

  const handleGenerateSummary = async () => {
    await generateSummary();
  };

  const handleRefreshSummary = async () => {
    await refreshSummary();
  };

  const handleClose = () => {
    onOpenChange(false);
  };

  const getSentimentColor = (sentiment?: string) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive':
        return 'success';
      case 'negative':
        return 'destructive';
      case 'neutral':
        return 'secondary';
      default:
        return 'secondary';
    }
  };

  const formatDuration = (minutes?: number) => {
    if (!minutes) return 'N/A';
    if (minutes < 60) return `${Math.round(minutes)}m`;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = Math.round(minutes % 60);
    return `${hours}h ${remainingMinutes}m`;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={styles.modalContent}>
        <DialogHeader className={styles.modalHeader}>
          <DialogTitle className={styles.modalTitle}>
            <div className="flex items-center gap-2">
              <DocumentTextIcon className="w-5 h-5" />
              <span>Conversation Summary</span>
              {conversationTitle && (
                <span className="text-muted-foreground font-normal">
                  - {conversationTitle}
                </span>
              )}
            </div>
          </DialogTitle>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleClose}
            className={styles.closeButton}
          >
            <XMarkIcon className="w-4 h-4" />
          </Button>
        </DialogHeader>

        <div className={styles.modalBody}>
          {/* Action Buttons */}
          <div className={styles.actionButtons}>
            <Button
              onClick={handleGenerateSummary}
              disabled={isGenerating}
              className={styles.generateButton}
            >
              {isGenerating ? (
                <>
                  <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <SparklesIcon className="w-4 h-4 mr-2 sparkle-icon" />
                  Generate Summary
                </>
              )}
            </Button>
            
            {summary && (
              <Button
                variant="outline"
                onClick={handleRefreshSummary}
                disabled={isLoading}
                className={styles.refreshButton}
              >
                <ArrowPathIcon className="w-4 h-4 mr-2" />
                Refresh
              </Button>
            )}
          </div>

          {/* Loading State */}
          {(isLoading || isGenerating) && !summary && (
            <div className={styles.loadingState}>
              <ArrowPathIcon className="w-6 h-6 animate-spin" />
              <p>
                {isGenerating 
                  ? 'Analyzing conversation and generating summary...' 
                  : 'Loading summary...'
                }
              </p>
              {isGenerating && (
                <p className="text-sm text-muted-foreground mt-2">
                  This may take up to 2 minutes for long conversations
                </p>
              )}
            </div>
          )}

          {/* Error State */}
          {error && !summary && (
            <div className={styles.errorState}>
              <p className="text-destructive">Error: {error}</p>
              <Button
                variant="outline"
                onClick={handleGenerateSummary}
                disabled={isGenerating}
                size="sm"
              >
                Try Again
              </Button>
            </div>
          )}

          {/* Summary Content */}
          {summary && (
            <div className={styles.summaryContent}>
              {/* Metadata */}
              <div className={styles.metadata}>
                <div className={styles.metadataItem}>
                  <ClockIcon className="w-4 h-4" />
                  <span>Generated {formatRelativeTime(new Date(summary.generated_at))}</span>
                </div>
                
                <div className={styles.metadataItem}>
                  <ChatBubbleLeftRightIcon className="w-4 h-4" />
                  <span>{summary.message_count} messages</span>
                </div>
                
                <div className={styles.metadataItem}>
                  <SparklesIcon className="w-4 h-4" />
                  <span>{summary.ai_message_count} AI messages</span>
                </div>
                
                {summary.duration_minutes && (
                  <div className={styles.metadataItem}>
                    <ClockIcon className="w-4 h-4" />
                    <span>Duration: {formatDuration(summary.duration_minutes)}</span>
                  </div>
                )}
                
                {processingTime > 0 && (
                  <div className={styles.metadataItem}>
                    <SparklesIcon className="w-4 h-4" />
                    <span>Processed in {(processingTime / 1000).toFixed(1)}s</span>
                  </div>
                )}
              </div>

              <div className={styles.separator} />

              {/* Customer */}
              {summary.customer && (
                <div className={styles.customerSection}>
                  <h4 className={styles.sectionTitle}>Customer</h4>
                  <div className={styles.customerInfo}>
                    <div className={styles.customerItem}>
                      <span className={styles.customerName}>{summary.customer.name}</span>
                      <span className={styles.customerPhone}>{summary.customer.phone}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Human Agents */}
              {summary.human_agents && summary.human_agents.length > 0 && (
                <div className={styles.agentsSection}>
                  <h4 className={styles.sectionTitle}>Human Agents</h4>
                  <div className={styles.agentsList}>
                    {summary.human_agents.map((agent, index) => (
                      <div key={index} className={styles.agentItem}>
                        <span className={styles.agentName}>{agent.name}</span>
                        <span className={styles.agentEmail}>{agent.email}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Sentiment */}
              {summary.sentiment && (
                <div className={styles.sentimentSection}>
                  <h4 className={styles.sectionTitle}>Customer Sentiment</h4>
                  <div className={styles.sentimentDisplay}>
                    {summary.sentiment_emoji && (
                      <span className={styles.sentimentEmoji}>{summary.sentiment_emoji}</span>
                    )}
                    <Badge variant={getSentimentColor(summary.sentiment)}>
                      {summary.sentiment}
                    </Badge>
                  </div>
                </div>
              )}

              {/* Topics */}
              {summary.topics && summary.topics.length > 0 && (
                <div className={styles.topicsSection}>
                  <h4 className={styles.sectionTitle}>Topics Discussed</h4>
                  <div className={styles.topicsList}>
                    {summary.topics.map((topic, index) => (
                      <Badge key={index} variant="outline" className={styles.topicBadge}>
                        {topic}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Key Points */}
              {summary.key_points && summary.key_points.length > 0 && (
                <div className={styles.keyPointsSection}>
                  <h4 className={styles.sectionTitle}>Key Points</h4>
                  <ul className={styles.keyPointsList}>
                    {summary.key_points.map((point, index) => (
                      <li key={index} className={styles.keyPoint}>
                        {point}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Main Summary */}
              <div className={styles.mainSummary}>
                <h4 className={styles.sectionTitle}>Summary</h4>
                <div className={styles.markdownContent}>
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm, remarkBreaks]}
                    components={{
                      code({ node, inline, className, children, ...props }) {
                        const match = /language-(\w+)/.exec(className || '');
                        return !inline && match ? (
                          <SyntaxHighlighter
                            style={oneDark}
                            language={match[1]}
                            PreTag="div"
                            {...props}
                          >
                            {String(children).replace(/\n$/, '')}
                          </SyntaxHighlighter>
                        ) : (
                          <code className={className} {...props}>
                            {children}
                          </code>
                        );
                      },
                      h1: ({ children }) => <h1 className={styles.markdownH1}>{children}</h1>,
                      h2: ({ children }) => <h2 className={styles.markdownH2}>{children}</h2>,
                      h3: ({ children }) => <h3 className={styles.markdownH3}>{children}</h3>,
                      p: ({ children }) => <p className={styles.markdownP}>{children}</p>,
                      ul: ({ children }) => <ul className={styles.markdownUl}>{children}</ul>,
                      ol: ({ children }) => <ol className={styles.markdownOl}>{children}</ol>,
                      li: ({ children }) => <li className={styles.markdownLi}>{children}</li>,
                      blockquote: ({ children }) => (
                        <blockquote className={styles.markdownBlockquote}>{children}</blockquote>
                      ),
                      strong: ({ children }) => <strong className={styles.markdownStrong}>{children}</strong>,
                      em: ({ children }) => <em className={styles.markdownEm}>{children}</em>,
                      a: ({ href, children }) => (
                        <a href={href} className={styles.markdownLink} target="_blank" rel="noopener noreferrer">
                          {children}
                        </a>
                      )
                    }}
                  >
                    {summary.summary}
                  </ReactMarkdown>
                </div>
              </div>
            </div>
          )}

          {/* Empty State */}
          {!summary && !isLoading && !error && (
            <div className={styles.emptyState}>
              <DocumentTextIcon className="w-12 h-12 text-muted-foreground" />
              <h3 className={styles.emptyTitle}>No Summary Available</h3>
              <p className={styles.emptyDescription}>
                Generate an AI-powered summary of this conversation to get key insights and highlights.
              </p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
