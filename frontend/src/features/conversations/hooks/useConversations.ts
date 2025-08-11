/**
 * React hooks for managing conversation state and API calls.
 * Uses TanStack Query for data fetching and caching.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ConversationsApi } from '../api/conversationsApi';
import {
  ConversationFilters,
  CreateConversationRequest,
  UpdateConversationRequest,
  TransferConversationRequest,
  ConversationStats,
  Conversation,
} from '../models/conversation';
import { toast } from '@/components/feedback/Toast';
import { createApiErrorHandler } from '@/lib/http';

// Query keys for conversations
export const conversationQueryKeys = {
  all: ['conversations'] as const,
  lists: () => ['conversations', 'list'] as const,
  list: (filters: ConversationFilters) => ['conversations', 'list', filters] as const,
  details: () => ['conversations', 'detail'] as const,
  detail: (id: string) => ['conversations', 'detail', id] as const,
  stats: () => ['conversations', 'stats'] as const,
};

/**
 * Hook to fetch conversations with filters
 */
export function useConversations(filters: ConversationFilters) {
  return useQuery({
    queryKey: conversationQueryKeys.list(filters),
    queryFn: () => ConversationsApi.getConversations(filters),
    staleTime: 30 * 1000,
    enabled: !!filters,
  });
}

/**
 * Hook to fetch a single conversation
 */
export function useConversation(conversationId: string) {
  return useQuery<Conversation>({
    queryKey: conversationQueryKeys.detail(conversationId),
    queryFn: () => ConversationsApi.getConversation(conversationId),
    staleTime: 30 * 1000,
    enabled: !!conversationId,
  });
}

/**
 * Hook to fetch conversation statistics
 */
export function useConversationStats() {
  return useQuery({
    queryKey: conversationQueryKeys.stats(),
    queryFn: () => ConversationsApi.getConversationStats(),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook to create a new conversation
 */
export function useCreateConversation() {
  const queryClient = useQueryClient();
  const handleError = createApiErrorHandler((msg: string) => toast.error(msg));

  return useMutation({
    mutationFn: (data: CreateConversationRequest) => ConversationsApi.createConversation(data),
    onSuccess: () => {
      // Invalidate and refetch conversations list
      queryClient.invalidateQueries({ queryKey: conversationQueryKeys.lists() });
      toast.success('Conversation created successfully');
    },
    onError: handleError,
  });
}

/**
 * Hook to update a conversation
 */
export function useUpdateConversation() {
  const queryClient = useQueryClient();
  const handleError = createApiErrorHandler((msg: string) => toast.error(msg));

  return useMutation({
    mutationFn: ({ 
      conversationId, 
      data 
    }: { 
      conversationId: string; 
      data: UpdateConversationRequest 
    }) => ConversationsApi.updateConversation(conversationId, data),
    onSuccess: (_, variables) => {
      // Invalidate and refetch conversation details and list
      queryClient.invalidateQueries({ 
        queryKey: conversationQueryKeys.detail(variables.conversationId) 
      });
      queryClient.invalidateQueries({ queryKey: conversationQueryKeys.lists() });
      toast.success('Conversation updated successfully');
    },
    onError: handleError,
  });
}

/**
 * Hook to close a conversation
 */
export function useCloseConversation() {
  const queryClient = useQueryClient();
  const handleError = createApiErrorHandler((msg: string) => toast.error(msg));

  return useMutation({
    mutationFn: (conversationId: string) => ConversationsApi.closeConversation(conversationId),
    onSuccess: (_, conversationId) => {
      // Invalidate and refetch conversation details and list
      queryClient.invalidateQueries({ 
        queryKey: conversationQueryKeys.detail(conversationId) 
      });
      queryClient.invalidateQueries({ queryKey: conversationQueryKeys.lists() });
      toast.success('Conversation closed successfully');
    },
    onError: handleError,
  });
}

/**
 * Hook to transfer a conversation
 */
export function useTransferConversation() {
  const queryClient = useQueryClient();
  const handleError = createApiErrorHandler((msg: string) => toast.error(msg));

  return useMutation({
    mutationFn: ({ 
      conversationId, 
      data 
    }: { 
      conversationId: string; 
      data: TransferConversationRequest 
    }) => ConversationsApi.transferConversation(conversationId, data),
    onSuccess: (_, variables) => {
      // Invalidate and refetch conversation details and list
      queryClient.invalidateQueries({ 
        queryKey: conversationQueryKeys.detail(variables.conversationId) 
      });
      queryClient.invalidateQueries({ queryKey: conversationQueryKeys.lists() });
      toast.success('Conversation transferred successfully');
    },
    onError: handleError,
  });
}