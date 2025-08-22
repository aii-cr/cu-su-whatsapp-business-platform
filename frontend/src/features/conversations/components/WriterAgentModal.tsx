/**
 * Writer Agent Modal component with glass style.
 * Provides interface for generating AI-powered responses.
 */

import * as React from 'react';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/feedback/LoadingSpinner';
import { cn } from '@/lib/utils';
import { 
  SparklesIcon,
  PaperAirplaneIcon,
  XMarkIcon,
  ArrowPathIcon,
  CheckIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { useWriterAgent } from '../hooks/useWriterAgent';
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
  const [isEditing, setIsEditing] = useState(false);

  const {
    isLoading,
    error,
    lastResponse,
    generateResponse,
    generateContextualResponse,
    clearError,
    clearResponse,
    setCustomError
  } = useWriterAgent({
    onSuccess: (response) => {
      setGeneratedResponse(response.response);
      setIsEditing(true);
      onResponseGenerated(response.response);
    },
    onError: (error) => {
      console.error('Writer Agent error:', error);
    }
  });

  // Clear state when modal opens/closes
  useEffect(() => {
    if (open) {
      setCustomQuery('');
      setGeneratedResponse('');
      setIsEditing(false);
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
      await generateContextualResponse({ conversation_id: conversationId });
    } catch (error) {
      // Error handling is done in the hook
    }
  };

  const handleGenerateCustom = async () => {
    if (!customQuery.trim()) return;

    try {
      await generateResponse({
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
      <div className={styles.modal}>
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
              {lastResponse?.metadata && (
                <div className={styles.loadingMeta}>
                  Iteration {lastResponse.metadata.iterations || 0} - Ensuring helpfulness
                </div>
              )}
            </div>
          )}

          {/* Generated Response */}
          {generatedResponse && (
            <div className={styles.responseSection}>
              <div className={styles.responseHeader}>
                <h4 className={styles.sectionTitle}>Generated Response</h4>
                {lastResponse?.metadata && (
                  <div className={styles.responseMeta}>
                    <span className={styles.responseMetaItem}>
                      ✓ {lastResponse.metadata.iterations} iterations
                    </span>
                    <span className={styles.responseMetaItem}>
                      ⚡ {lastResponse.metadata.processing_time_ms}ms
                    </span>
                    <span className={styles.responseMetaItem}>
                      {lastResponse.metadata.helpfulness_score === 'Y' ? '✅ Helpful' : '⚠️ Needs review'}
                    </span>
                  </div>
                )}
              </div>
              
              <textarea
                value={generatedResponse}
                onChange={(e) => setGeneratedResponse(e.target.value)}
                disabled={!isEditing}
                className={cn(
                  styles.responseTextarea,
                  !isEditing && styles.responseTextareaReadOnly
                )}
                rows={6}
                placeholder="Generated response will appear here..."
              />
              
              <div className={styles.responseActions}>
                <Button
                  variant="outline"
                  onClick={() => setIsEditing(!isEditing)}
                  className={styles.editButton}
                >
                  {isEditing ? (
                    <>
                      <CheckIcon className="w-4 h-4 mr-2" />
                      Done Editing
                    </>
                  ) : (
                    <>
                      <ArrowPathIcon className="w-4 h-4 mr-2" />
                      Edit Response
                    </>
                  )}
                </Button>
                
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
