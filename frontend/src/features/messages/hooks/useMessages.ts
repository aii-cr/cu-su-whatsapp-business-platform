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
    staleTime: 30 * 1000, // 30 seconds
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
      
      // Don't cancel queries - let WebSocket updates work normally
      // The optimistic message will be handled by the VirtualizedMessageList component
      // This prevents conflicts between the hook's optimistic updates and the component's state
      
      console.log('🔄 [OPTIMISTIC] Message mutation started, optimistic update handled by VirtualizedMessageList');
      return { conversationId };
    },
    onSuccess: (response, variables, context) => {
      const conversationId = variables.conversation_id;
      const sentMessage = response.message; // The actual message object is nested in the response
      
      if (!conversationId) {
        console.error('No conversation ID available in success callback');
        return;
      }
      
      // The optimistic message update is handled by the VirtualizedMessageList component
      // This prevents conflicts and ensures smooth UX
      console.log('✅ [MESSAGE] Sent successfully, optimistic update handled by VirtualizedMessageList');
      toast.success('Message sent');
    },
    onError: (error, variables, context) => {
      const conversationId = variables.conversation_id;
      
      if (!conversationId) {
        handleError(error);
        return;
      }
      
      // The optimistic message removal is handled by the VirtualizedMessageList component
      // This prevents conflicts and ensures smooth UX
      console.log('❌ [MESSAGE] Failed to send message, optimistic removal handled by VirtualizedMessageList');
      handleError(error);
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
    }) => MessagesApi.sendMediaMessage(conversationId, mediaFile, caption),
    onSuccess: (response) => {
      // Invalidate and refetch messages for the conversation
      if (response.message?.conversation_id) {
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