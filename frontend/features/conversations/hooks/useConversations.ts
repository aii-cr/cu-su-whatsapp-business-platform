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
import { toast } from '@/components/ui/Toast';

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
    staleTime: 30 * 1000, // 30 seconds
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
    staleTime: 30 * 1000, // 30 seconds
    enabled: !!conversationId,
  });
}

/**
 * Hook to fetch conversation statistics
 */
export function useConversationStats() {
  return useQuery<ConversationStats>({
    queryKey: conversationQueryKeys.stats(),
    queryFn: () => ConversationsApi.getConversationStats(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to create a new conversation
 */
export function useCreateConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateConversationRequest) => ConversationsApi.createConversation(data),
    onSuccess: () => {
      // Invalidate and refetch conversations list
      queryClient.invalidateQueries({ queryKey: conversationQueryKeys.lists() });
      toast.success('Conversation created successfully');
    },
    onError: (error) => {
      console.error('Failed to create conversation:', error);
      toast.error('Failed to create conversation');
    },
  });
}

/**
 * Hook to update a conversation
 */
export function useUpdateConversation() {
  const queryClient = useQueryClient();

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
    onError: (error) => {
      console.error('Failed to update conversation:', error);
      toast.error('Failed to update conversation');
    },
  });
}

/**
 * Hook to close a conversation
 */
export function useCloseConversation() {
  const queryClient = useQueryClient();

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
    onError: (error) => {
      console.error('Failed to close conversation:', error);
      toast.error('Failed to close conversation');
    },
  });
}

/**
 * Hook to transfer a conversation
 */
export function useTransferConversation() {
  const queryClient = useQueryClient();

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
    onError: (error) => {
      console.error('Failed to transfer conversation:', error);
      toast.error('Failed to transfer conversation');
    },
  });
}