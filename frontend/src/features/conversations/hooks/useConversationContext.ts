/**
 * Hook for managing conversation context and AI memory
 */

import { useState, useEffect, useCallback } from 'react';

interface ConversationContext {
  conversation_id: string;
  history: Array<{
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    message_id: string;
  }>;
  summary: string;
  session_data: Record<string, any>;
  last_activity?: string;
  memory_size: number;
}

interface UseConversationContextReturn {
  context: ConversationContext | null;
  loading: boolean;
  error: string | null;
  refreshContext: () => Promise<void>;
  clearMemory: () => Promise<void>;
  isClearing: boolean;
}

export const useConversationContext = (conversationId: string): UseConversationContextReturn => {
  const [context, setContext] = useState<ConversationContext | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isClearing, setIsClearing] = useState(false);

  const fetchContext = useCallback(async () => {
    if (!conversationId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/ai/memory/conversation/${conversationId}/context`);
      const data = await response.json();
      
      if (data.success) {
        setContext(data.context);
      } else {
        setError(data.error || 'Failed to load conversation context');
      }
    } catch (err) {
      setError('Failed to load conversation context');
      console.error('Error fetching conversation context:', err);
    } finally {
      setLoading(false);
    }
  }, [conversationId]);

  const clearMemory = useCallback(async () => {
    if (!conversationId) return;
    
    setIsClearing(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/ai/memory/conversation/${conversationId}/memory`, {
        method: 'DELETE'
      });
      const data = await response.json();
      
      if (data.success) {
        // Refresh context after clearing
        await fetchContext();
      } else {
        setError(data.error || 'Failed to clear conversation memory');
      }
    } catch (err) {
      setError('Failed to clear conversation memory');
      console.error('Error clearing conversation memory:', err);
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

