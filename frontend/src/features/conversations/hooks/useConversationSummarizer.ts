/**
 * Hook for conversation summarization functionality.
 */

import { useState, useCallback } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { toast } from '@/components/feedback/Toast';
import { 
  SummarizerApi, 
  ConversationSummaryRequest, 
  ConversationSummaryResponse,
  SummarizeResponse 
} from '../api/summarizerApi';

export interface UseConversationSummarizerOptions {
  conversationId: string;
  summaryType?: string;
  includeMetadata?: boolean;
}

export interface UseConversationSummarizerReturn {
  // State
  isLoading: boolean;
  isGenerating: boolean;
  summary: ConversationSummaryResponse | null;
  error: string | null;
  
  // Actions
  generateSummary: () => Promise<void>;
  refreshSummary: () => Promise<void>;
  clearSummary: () => void;
  
  // Data
  processingTime: number;
  lastGenerated: string | null;
}

export function useConversationSummarizer({
  conversationId,
  summaryType = 'general',
  includeMetadata = true
}: UseConversationSummarizerOptions): UseConversationSummarizerReturn {
  const [localSummary, setLocalSummary] = useState<ConversationSummaryResponse | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);
  const [processingTime, setProcessingTime] = useState(0);
  const [lastGenerated, setLastGenerated] = useState<string | null>(null);

  // Query for existing summary (enabled when conversationId is available)
  const {
    data: existingSummary,
    isLoading: isLoadingExisting,
    error: existingError,
    refetch: refetchSummary
  } = useQuery({
    queryKey: ['conversation-summary', conversationId, summaryType, includeMetadata],
    queryFn: () => SummarizerApi.getConversationSummary(conversationId, summaryType, includeMetadata),
    enabled: !!conversationId, // Enable when conversationId is available
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2
  });

  // Mutation for generating new summary
  const generateMutation = useMutation({
    mutationFn: async (request: ConversationSummaryRequest) => {
      const startTime = Date.now();
      // Show initial loading toast
      toast.info('Starting conversation analysis...', { duration: 2000 });
      
      const result = await SummarizerApi.summarizeConversation(request);
      const endTime = Date.now();
      return { ...result, processingTime: endTime - startTime };
    },
    onSuccess: (data: SummarizeResponse & { processingTime: number }) => {
      if (data.success && data.summary) {
        setLocalSummary(data.summary);
        setLocalError(null);
        setProcessingTime(data.processingTime);
        setLastGenerated(new Date().toISOString());
        toast.success(`Summary generated in ${(data.processingTime / 1000).toFixed(1)}s!`);
      } else {
        setLocalError(data.error || 'Failed to generate summary');
        toast.error(data.error || 'Failed to generate summary');
      }
    },
    onError: (error: any) => {
      let errorMessage = 'Failed to generate summary';
      
      if (error?.name === 'AbortError' || error?.message?.includes('timeout')) {
        errorMessage = 'Summarization timed out. Please try again.';
      } else if (error?.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error?.message) {
        errorMessage = error.message;
      }
      
      setLocalError(errorMessage);
      toast.error(errorMessage);
    }
  });

  // Generate new summary
  const generateSummary = useCallback(async () => {
    if (!conversationId) {
      toast.error('No conversation selected');
      return;
    }

    const request: ConversationSummaryRequest = {
      conversation_id: conversationId,
      summary_type: summaryType,
      include_metadata: includeMetadata
    };

    await generateMutation.mutateAsync(request);
  }, [conversationId, summaryType, includeMetadata, generateMutation]);

  // Refresh existing summary
  const refreshSummary = useCallback(async () => {
    if (!conversationId) {
      toast.error('No conversation selected');
      return;
    }
    await refetchSummary();
  }, [refetchSummary, conversationId]);

  // Clear local summary
  const clearSummary = useCallback(() => {
    setLocalSummary(null);
    setLocalError(null);
    setProcessingTime(0);
    setLastGenerated(null);
  }, []);

  // Determine which summary to show (local takes precedence)
  const summary = localSummary || (existingSummary?.success && existingSummary.summary ? existingSummary.summary : null);
  const error = localError || (existingError ? existingError.message : null);
  const isLoading = isLoadingExisting;
  const isGenerating = generateMutation.isPending;



  return {
    // State
    isLoading,
    isGenerating,
    summary,
    error,
    
    // Actions
    generateSummary,
    refreshSummary,
    clearSummary,
    
    // Data
    processingTime,
    lastGenerated
  };
}
