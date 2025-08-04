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
import { useNotifications } from '@/components/feedback/NotificationSystem';
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
  const { showError } = useNotifications();
  const handleError = createApiErrorHandler(showError);

  return useQuery({
    queryKey: conversationQueryKeys.list(filters),
    queryFn: () => ConversationsApi.getConversations(filters),
    staleTime: 30 * 1000, // 30 seconds
    enabled: !!filters,
    onError: handleError,
  });
}

/**
 * Hook to fetch a single conversation
 */
export function useConversation(conversationId: string) {
  const { showError } = useNotifications();
  const handleError = createApiErrorHandler(showError);

  return useQuery<Conversation>({
    queryKey: conversationQueryKeys.detail(conversationId),
    queryFn: () => ConversationsApi.getConversation(conversationId),
    staleTime: 30 * 1000, // 30 seconds
    enabled: !!conversationId,
    onError: handleError,
  });
}

/**
 * Hook to fetch conversation statistics
 */
export function useConversationStats() {
  const { showError } = useNotifications();
  const handleError = createApiErrorHandler(showError);

  return useQuery<ConversationStats>({
    queryKey: conversationQueryKeys.stats(),
    queryFn: () => ConversationsApi.getConversationStats(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    onError: handleError,
  });
}

/**
 * Hook to create a new conversation
 */
export function useCreateConversation() {
  const queryClient = useQueryClient();
  const { showSuccess, showError } = useNotifications();
  const handleError = createApiErrorHandler(showError);

  return useMutation({
    mutationFn: (data: CreateConversationRequest) => ConversationsApi.createConversation(data),
    onSuccess: () => {
      // Invalidate and refetch conversations list
      queryClient.invalidateQueries({ queryKey: conversationQueryKeys.lists() });
      showSuccess('Conversation created successfully');
    },
    onError: handleError,
  });
}

/**
 * Hook to update a conversation
 */
export function useUpdateConversation() {
  const queryClient = useQueryClient();
  const { showSuccess, showError } = useNotifications();
  const handleError = createApiErrorHandler(showError);

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
      showSuccess('Conversation updated successfully');
    },
    onError: handleError,
  });
}

/**
 * Hook to close a conversation
 */
export function useCloseConversation() {
  const queryClient = useQueryClient();
  const { showSuccess, showError } = useNotifications();
  const handleError = createApiErrorHandler(showError);

  return useMutation({
    mutationFn: (conversationId: string) => ConversationsApi.closeConversation(conversationId),
    onSuccess: (_, conversationId) => {
      // Invalidate and refetch conversation details and list
      queryClient.invalidateQueries({ 
        queryKey: conversationQueryKeys.detail(conversationId) 
      });
      queryClient.invalidateQueries({ queryKey: conversationQueryKeys.lists() });
      showSuccess('Conversation closed successfully');
    },
    onError: handleError,
  });
}

/**
 * Hook to transfer a conversation
 */
export function useTransferConversation() {
  const queryClient = useQueryClient();
  const { showSuccess, showError } = useNotifications();
  const handleError = createApiErrorHandler(showError);

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
      showSuccess('Conversation transferred successfully');
    },
    onError: handleError,
  });
}