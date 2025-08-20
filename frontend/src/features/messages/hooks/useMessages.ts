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
  Message,
} from '../models/message';
import { toast } from '@/components/feedback/Toast';
import { createApiErrorHandler } from '@/lib/http';
import { useAuthStore } from '@/lib/store';

// Query keys for messages
export const messageQueryKeys = {
  all: ['messages'] as const,
  conversation: (conversationId: string) => ['messages', 'conversation', conversationId] as const,
  conversationMessages: (conversationId: string, filters?: Omit<MessageFilters, 'conversation_id'>) => 
    ['messages', 'conversation', conversationId, filters] as const,
};

/**
 * Hook to fetch messages for a conversation with cursor-based infinite scroll
 */
export function useMessages(conversationId: string, limit: number = 50) {
  const handleError = createApiErrorHandler((msg: string) => toast.error(msg));

  const query = useInfiniteQuery<{
    messages: Message[];
    next_cursor: string | null;
    has_more: boolean;
    anchor: string;
    cache_hit: boolean;
  }>({
    queryKey: messageQueryKeys.conversationMessages(conversationId, { limit }),
    queryFn: async ({ pageParam }) => {
      return MessagesApi.getMessagesCursor(
        conversationId,
        limit,
        pageParam as string | undefined // cursor
      );
    },
    getNextPageParam: (lastPage) => {
      return lastPage.has_more ? lastPage.next_cursor : undefined;
    },
    staleTime: 0, // Disable stale caching for messages
    gcTime: 0, // Disable garbage collection caching for messages
    enabled: !!conversationId,
    initialPageParam: undefined, // Start with no cursor to get latest messages
  });

  // Handle errors manually
  if (query.error) {
    handleError(query.error);
  }

  return query;
}

/**
 * Hook to send a message with optimistic updates
 */
export function useSendMessage() {
  const queryClient = useQueryClient();
  const handleError = createApiErrorHandler((msg: string) => toast.error(msg));
  const { user } = useAuthStore();

  return useMutation({
    mutationFn: (data: SendMessageRequest) => MessagesApi.sendMessage(data),
    onMutate: async (variables) => {
      const conversationId = variables.conversation_id;
      
      if (!conversationId) {
        throw new Error('Conversation ID is required');
      }
      
      console.log('🚀 [OPTIMISTIC] Starting optimistic update for conversation:', conversationId);
      
      // Cancel any outgoing refetches (so they don't overwrite our optimistic update)
      await queryClient.cancelQueries({
        queryKey: messageQueryKeys.conversationMessages(conversationId, { limit: 50 }),
      });

      // Snapshot the previous value
      const previousMessages = queryClient.getQueryData(
        messageQueryKeys.conversationMessages(conversationId, { limit: 50 })
      );

      // Note: Optimistic message is now handled by VirtualizedMessageList component
      // to avoid conflicts and ensure smooth UX
      console.log('🚀 [OPTIMISTIC] Optimistic message handled by VirtualizedMessageList');
      
      // Return a context object with the snapshotted value
      return { previousMessages };
    },
    onSuccess: (response, variables, context) => {
      const conversationId = variables.conversation_id;
      const sentMessage = response.message; // Extract message from response
      
      if (!conversationId) {
        console.error('No conversation ID available in success callback');
        return;
      }
      
      console.log('✅ [MESSAGE] Message sent successfully:', sentMessage._id);
      console.log('✅ [MESSAGE] Real message data:', sentMessage);
      
      // Note: Optimistic message update is now handled by the conversation page
      // which calls updateOptimisticMessage on the VirtualizedMessageList
      console.log('✅ [MESSAGE] Optimistic message update handled by conversation page');
    },
    onError: (error, variables, context) => {
      const conversationId = variables.conversation_id;
      
      if (!conversationId) {
        handleError(error);
        return;
      }
      
      console.error('❌ [MESSAGE] Message send failed:', error);
      
      // If the mutation fails, use the context returned from onMutate to roll back
      if (context?.previousMessages) {
        queryClient.setQueryData(
          messageQueryKeys.conversationMessages(conversationId, { limit: 50 }),
          context.previousMessages
        );
        console.log('❌ [OPTIMISTIC] Rolled back optimistic message due to error');
      }
      
      handleError(error);
    },
    onSettled: (data, error, variables) => {
      // Don't invalidate cache here - let WebSocket handle real-time updates
      // This prevents conflicts between mutation and WebSocket updates
      console.log('✅ [MESSAGE] Message mutation settled, WebSocket will handle updates');
    },
  });
}

/**
 * Hook to send media message (placeholder)
 */
export function useSendMediaMessage() {
  const queryClient = useQueryClient();
  const handleError = createApiErrorHandler((msg: string) => toast.error(msg));

  return useMutation({
    mutationFn: ({ 
      conversationId, 
      mediaFile, 
      caption 
    }: { 
      conversationId: string; 
      mediaFile: File; 
      caption?: string 
    }) => {
      // TODO: Implement media message sending
      console.log('Media message sending not implemented yet');
      return Promise.resolve({ message: null });
    },
    onSuccess: (response: any) => {
      // Invalidate and refetch messages for the conversation
      if (response?.message?.conversation_id) {
        queryClient.invalidateQueries({
          queryKey: messageQueryKeys.conversation(response.message.conversation_id),
        });
      }

      toast.success('Media message sent successfully');
    },
    onError: handleError,
  });
}

/**
 * Hook to get message templates
 */
export function useMessageTemplates() {
  const handleError = createApiErrorHandler((msg: string) => toast.error(msg));

  const query = useQuery({
    queryKey: ['messages', 'templates'],
    queryFn: () => MessagesApi.getTemplates(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Handle errors manually
  if (query.error) {
    handleError(query.error);
  }

  return query;
}