/**
 * Writer Agent Modal component with glass style.
 * Provides interface for generating AI-powered responses.
 */

import * as React from 'react';
import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/feedback/LoadingSpinner';
import { cn } from '@/lib/utils';
import { 
  SparklesIcon,
  PaperAirplaneIcon,
  XMarkIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  ChevronDownIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline';
import { useWriterAgent } from '../hooks/useWriterAgent';
import { Markdown } from '@/components/ui/Markdown';
import styles from './WriterAgentModal.module.scss';

export interface WriterAgentModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  conversationId?: string;
  onResponseGenerated: (response: string) => void;
  onSendMessage: (text: string) => void;
  className?: string;
}

export function WriterAgentModal({
  open,
  onOpenChange,
  conversationId,
  onResponseGenerated,
  onSendMessage,
  className
}: WriterAgentModalProps) {
  const [customQuery, setCustomQuery] = useState('');
  const [generatedResponse, setGeneratedResponse] = useState('');
  const [reasoningText, setReasoningText] = useState('');
  const [isReasoningExpanded, setIsReasoningExpanded] = useState(false);
  
  const modalRef = useRef<HTMLDivElement>(null);

  const {
    isLoading,
    error,
    lastResponse,
    lastStructuredResponse,
    generateResponse,
    generateContextualResponse,
    generateStructuredResponse,
    generateStructuredContextualResponse,
    clearError,
    clearResponse,
    setCustomError
  } = useWriterAgent({
    onSuccess: (response) => {
      setGeneratedResponse(response.response);
      setReasoningText('');
      // Don't call onResponseGenerated here - only update the textarea
    },
    onStructuredSuccess: (response) => {
      if (response.structured_response) {
        setGeneratedResponse(response.structured_response.customer_response);
        setReasoningText(response.structured_response.reason);
        // Don't call onResponseGenerated here - only update the textarea
      } else {
        // Fallback to raw response if structured parsing failed
        setGeneratedResponse(response.raw_response);
        setReasoningText('');
        // Don't call onResponseGenerated here - only update the textarea
      }
    },
    onError: (error) => {
      console.error('Writer Agent error:', error);
    }
  });

  // Handle click outside to close modal
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(event.target as Node)) {
        onOpenChange(false);
      }
    };

    if (open) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [open, onOpenChange]);

  // Clear state when modal opens/closes
  useEffect(() => {
    if (open) {
      setCustomQuery('');
      setGeneratedResponse('');
      setReasoningText('');
      setIsReasoningExpanded(false);
      clearError();
      clearResponse();
    }
  }, [open, clearError, clearResponse]);

  const handleGenerateContextual = async () => {
    if (!conversationId) {
      setCustomError('Please select a conversation first to generate a contextual response.');
      return;
    }
    
    try {
      await generateStructuredContextualResponse({ conversation_id: conversationId });
    } catch (error) {
      // Error handling is done in the hook
    }
  };

  const handleGenerateCustom = async () => {
    if (!customQuery.trim()) return;

    try {
      await generateStructuredResponse({
        query: customQuery,
        conversation_id: conversationId
      });
    } catch (error) {
      // Error handling is done in the hook
    }
  };

  const handleSendResponse = () => {
    if (generatedResponse.trim()) {
      onSendMessage(generatedResponse);
      onOpenChange(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleGenerateCustom();
    }
  };

  if (!open) return null;

  return (
    <div className={cn(styles.overlay, className)}>
      <div ref={modalRef} className={styles.modal}>
        {/* Header */}
        <div className={styles.header}>
          <div className={styles.titleSection}>
            <SparklesIcon className={styles.titleIcon} />
            <h3 className={styles.title}>Writer Agent</h3>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onOpenChange(false)}
            className={styles.closeButton}
          >
            <XMarkIcon className="w-4 h-4" />
          </Button>
        </div>

        {/* Content */}
        <div className={styles.content}>
          {/* Contextual Response Section */}
          <div className={styles.section}>
            <h4 className={styles.sectionTitle}>Quick Actions</h4>
            <Button
              onClick={handleGenerateContextual}
              disabled={isLoading || !conversationId}
              className={styles.contextualButton}
            >
              {isLoading ? (
                <>
                  <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <SparklesIcon className="w-4 h-4 mr-2" />
                  Generate best possible response for current context
                </>
              )}
            </Button>
          </div>

          {/* Custom Query Section */}
          <div className={styles.section}>
            <h4 className={styles.sectionTitle}>Custom Request</h4>
            <div className={styles.querySection}>
              <Input
                value={customQuery}
                onChange={(e) => setCustomQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="e.g., 'I want to say that the service was put down but in a sympathetic way'"
                disabled={isLoading}
                className={styles.queryInput}
              />
              <Button
                onClick={handleGenerateCustom}
                disabled={isLoading || !customQuery.trim()}
                size="icon"
                className={styles.queryButton}
              >
                {isLoading ? (
                  <ArrowPathIcon className="w-4 h-4 animate-spin" />
                ) : (
                  <PaperAirplaneIcon className="w-4 h-4" />
                )}
              </Button>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className={styles.errorSection}>
              <ExclamationTriangleIcon className="w-4 h-4" />
              <span>{error}</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearError}
                className={styles.errorDismiss}
              >
                <XMarkIcon className="w-3 h-3" />
              </Button>
            </div>
          )}

          {/* Loading State */}
          {isLoading && (
            <div className={styles.loadingSection}>
              <LoadingSpinner size="sm" />
              <span>AI is analyzing and generating response...</span>
              {(lastResponse?.metadata || lastStructuredResponse?.metadata) && (
                <div className={styles.loadingMeta}>
                  Iteration {(lastStructuredResponse?.metadata.iterations || lastResponse?.metadata.iterations || 0)} - Ensuring helpfulness
                </div>
              )}
            </div>
          )}

          {/* Generated Response */}
          {generatedResponse && (
            <div className={styles.responseSection}>
              {/* AI Reasoning Section - Collapsible */}
              {reasoningText && (
                <div className={styles.reasoningSection}>
                  <button
                    onClick={() => setIsReasoningExpanded(!isReasoningExpanded)}
                    className={styles.reasoningToggle}
                  >
                    <div className={styles.reasoningToggleContent}>
                      {isReasoningExpanded ? (
                        <ChevronDownIcon className={styles.reasoningToggleIcon} />
                      ) : (
                        <ChevronRightIcon className={styles.reasoningToggleIcon} />
                      )}
                      <h4 className={styles.sectionTitle}>
                        {isReasoningExpanded ? 'Hide AI Strategy & Reasoning' : 'Show AI Strategy & Reasoning'}
                      </h4>
                    </div>
                  </button>
                  
                  <div className={cn(
                    styles.reasoningContent,
                    isReasoningExpanded && styles.reasoningContentExpanded
                  )}>
                    <Markdown content={reasoningText} />
                  </div>
                </div>
              )}
              
              <div className={styles.responseHeader}>
                <h4 className={styles.sectionTitle}>Customer Response</h4>
                {(lastResponse?.metadata || lastStructuredResponse?.metadata) && (
                  <div className={styles.responseMeta}>
                    <span className={styles.responseMetaItem}>
                      ✓ {(lastStructuredResponse?.metadata.iterations || lastResponse?.metadata.iterations || 0)} iterations
                    </span>
                    <span className={styles.responseMetaItem}>
                      ⚡ {(lastStructuredResponse?.metadata.processing_time_ms || lastResponse?.metadata.processing_time_ms || 0)}ms
                    </span>
                    <span className={styles.responseMetaItem}>
                      {(lastStructuredResponse?.metadata.helpfulness_score || lastResponse?.metadata.helpfulness_score) === 'Y' ? '✅ Helpful' : '⚠️ Needs review'}
                    </span>
                    {lastStructuredResponse?.metadata.has_structured_format && (
                      <span className={styles.responseMetaItem}>
                        🎯 Structured
                      </span>
                    )}
                  </div>
                )}
              </div>
              
              <textarea
                value={generatedResponse}
                onChange={(e) => setGeneratedResponse(e.target.value)}
                className={styles.responseTextarea}
                rows={6}
                placeholder="Generated response will appear here..."
                style={{ whiteSpace: 'pre-wrap' }}
              />
              
              <div className={styles.responseActions}>
                <Button
                  onClick={handleSendResponse}
                  disabled={!generatedResponse.trim()}
                  className={styles.sendButton}
                >
                  <PaperAirplaneIcon className="w-4 h-4 mr-2" />
                  Send to Customer
                </Button>
              </div>
            </div>
          )}

          {/* Help Text */}
          {!generatedResponse && !isLoading && (
            <div className={styles.helpSection}>
              <p className={styles.helpText}>
                💡 The Writer Agent will analyze conversation context, retrieve relevant information, 
                and generate professional responses. Responses go through a helpfulness validation loop 
                to ensure quality.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

