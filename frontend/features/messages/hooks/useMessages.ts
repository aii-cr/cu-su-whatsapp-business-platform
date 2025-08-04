/**
 * React hooks for managing message state and API calls.
 * Uses TanStack Query for data fetching and caching.
 */

import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import { MessagesApi } from '../api/messagesApi';
import {
  MessageFilters,
  SendMessageRequest,
  MessageListResponse,
} from '../models/message';
import { toast } from '@/components/ui/Toast';

// Query keys for messages
export const messageQueryKeys = {
  all: ['messages'] as const,
  conversation: (conversationId: string) => ['messages', 'conversation', conversationId] as const,
  conversationMessages: (conversationId: string, filters?: Omit<MessageFilters, 'conversation_id'>) => 
    ['messages', 'conversation', conversationId, filters] as const,
};

/**
 * Hook to fetch messages for a conversation with infinite scroll
 */
export function useMessages(conversationId: string, limit: number = 50) {
  return useInfiniteQuery<MessageListResponse>({
    queryKey: messageQueryKeys.conversationMessages(conversationId, { limit }),
    queryFn: async ({ pageParam = 0 }) => {
      return MessagesApi.getMessages({
        conversation_id: conversationId,
        limit,
        offset: pageParam as number,
      });
    },
    getNextPageParam: (lastPage, allPages) => {
      const nextOffset = allPages.length * limit;
      return nextOffset < lastPage.total ? nextOffset : undefined;
    },
    staleTime: 30 * 1000, // 30 seconds
    enabled: !!conversationId,
    initialPageParam: 0,
  });
}

/**
 * Hook to send a message
 */
export function useSendMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SendMessageRequest) => MessagesApi.sendMessage(data),
    onSuccess: (response, variables) => {
      // Invalidate and refetch messages for the conversation
      const conversationId = variables.conversation_id || response.conversation_id;
      queryClient.invalidateQueries({
        queryKey: messageQueryKeys.conversation(conversationId),
      });

      toast.success('Message sent successfully');
    },
    onError: (error) => {
      console.error('Failed to send message:', error);
      toast.error('Failed to send message');
    },
  });
}

/**
 * Hook to send media message (placeholder)
 */
export function useSendMediaMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ 
      conversationId, 
      mediaFile, 
      caption 
    }: { 
      conversationId: string; 
      mediaFile: File; 
      caption?: string 
    }) => MessagesApi.sendMediaMessage(conversationId, mediaFile, caption),
    onSuccess: (response) => {
      // Invalidate and refetch messages for the conversation
      queryClient.invalidateQueries({
        queryKey: messageQueryKeys.conversation(response.conversation_id),
      });

      toast.success('Media message sent successfully');
    },
    onError: (error) => {
      console.error('Failed to send media message:', error);
      toast.error('Failed to send media message');
    },
  });
}

/**
 * Hook to get message templates
 */
export function useMessageTemplates() {
  return useQuery({
    queryKey: ['messages', 'templates'],
    queryFn: () => MessagesApi.getTemplates(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}