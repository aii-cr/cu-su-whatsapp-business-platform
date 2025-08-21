/**
 * Hook for managing conversation context and AI memory
 */

import { useState, useEffect, useCallback } from 'react';
import { AiApi, ConversationContextData } from '../api/aiApi';

interface UseConversationContextReturn {
  context: ConversationContextData | null;
  loading: boolean;
  error: string | null;
  refreshContext: () => Promise<void>;
  clearMemory: () => Promise<void>;
  isClearing: boolean;
}

export const useConversationContext = (conversationId: string): UseConversationContextReturn => {
  const [context, setContext] = useState<ConversationContextData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isClearing, setIsClearing] = useState(false);

  const fetchContext = useCallback(async () => {
    if (!conversationId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await AiApi.getConversationContext(conversationId);
      
      if (response.success && response.context) {
        setContext(response.context);
      } else {
        setError(response.error || 'Failed to load conversation context');
      }
    } catch (err) {
      console.error('Error fetching conversation context:', err);
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to load conversation context');
      }
    } finally {
      setLoading(false);
    }
  }, [conversationId]);

  const clearMemory = useCallback(async () => {
    if (!conversationId) return;
    
    setIsClearing(true);
    setError(null);
    
    try {
      const response = await AiApi.clearConversationMemory(conversationId);
      
      if (response.success) {
        // Refresh context after clearing
        await fetchContext();
      } else {
        setError(response.error || 'Failed to clear conversation memory');
      }
    } catch (err) {
      console.error('Error clearing conversation memory:', err);
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to clear conversation memory');
      }
    } finally {
      setIsClearing(false);
    }
  }, [conversationId, fetchContext]);

  const refreshContext = useCallback(async () => {
    await fetchContext();
  }, [fetchContext]);

  useEffect(() => {
    fetchContext();
  }, [fetchContext]);

  return {
    context,
    loading,
    error,
    refreshContext,
    clearMemory,
    isClearing
  };
};
