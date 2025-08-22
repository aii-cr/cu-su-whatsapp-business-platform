/**
 * React hook for Writer Agent operations
 */

import { useState, useCallback } from 'react';
import { 
  generateWriterResponse, 
  generateContextualResponse as generateContextualResponseApi,
  WriterQueryRequest,
  ContextualResponseRequest,
  WriterResponse
} from '../api/writerApi';

export interface UseWriterAgentOptions {
  onSuccess?: (response: WriterResponse) => void;
  onError?: (error: Error) => void;
}

export function useWriterAgent(options?: UseWriterAgentOptions) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResponse, setLastResponse] = useState<WriterResponse | null>(null);

  const generateResponse = useCallback(async (request: WriterQueryRequest) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await generateWriterResponse(request);
      
      if (response.success) {
        setLastResponse(response);
        options?.onSuccess?.(response);
      } else {
        const errorMsg = response.error || 'Unknown error occurred';
        setError(errorMsg);
        options?.onError?.(new Error(errorMsg));
      }

      return response;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMsg);
      options?.onError?.(err instanceof Error ? err : new Error(errorMsg));
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [options]);

  const generateContextualResponse = useCallback(async (request: ContextualResponseRequest) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await generateContextualResponseApi(request);
      
      if (response.success) {
        setLastResponse(response);
        options?.onSuccess?.(response);
      } else {
        const errorMsg = response.error || 'Unknown error occurred';
        setError(errorMsg);
        options?.onError?.(new Error(errorMsg));
        // Don't set lastResponse for errors to avoid showing error in textarea
        return response;
      }

      return response;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMsg);
      options?.onError?.(err instanceof Error ? err : new Error(errorMsg));
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [options]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const clearResponse = useCallback(() => {
    setLastResponse(null);
  }, []);

  const setCustomError = useCallback((errorMessage: string) => {
    setError(errorMessage);
  }, []);

  return {
    isLoading,
    error,
    lastResponse,
    generateResponse,
    generateContextualResponse,
    clearError,
    clearResponse,
    setCustomError,
  };
}
