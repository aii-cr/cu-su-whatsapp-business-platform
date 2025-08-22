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
    staleTime: 60 * 1000, // Keep data fresh for 1 min to avoid flicker during optimistic flow
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    refetchOnMount: false,
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
      if (!conversationId) throw new Error('Conversation ID missing');

      await queryClient.cancelQueries({
        queryKey: messageQueryKeys.conversationMessages(conversationId, { limit: 50 }),
      });

      const previousData = queryClient.getQueryData(
        messageQueryKeys.conversationMessages(conversationId, { limit: 50 })
      );

      const optimisticId = `optimistic-${Date.now()}`;
      // Use current UTC time for optimistic messages
      const now = new Date();
      
      const optimisticMessage: Message = {
        _id: optimisticId,
        conversation_id: conversationId,
        type: 'text',
        direction: 'outbound',
        sender_role: 'agent',
        sender_id: user?._id ?? 'me',
        sender_name: user?.first_name ?? user?.email ?? 'Me',
        text_content: variables.text_content,
        status: 'sending',
        timestamp: now.toISOString(),
        created_at: now.toISOString(),
        updated_at: now.toISOString(),
      } as unknown as Message;

      queryClient.setQueryData(
        messageQueryKeys.conversationMessages(conversationId, { limit: 50 }),
        (old: any) => {
          if (!old) {
            return {
              pages: [{
                messages: [optimisticMessage],
                next_cursor: null,
                has_more: false,
                anchor: 'latest',
                cache_hit: false
              }],
            };
          }
          const newPages = [...old.pages];
          newPages[0] = {
            ...newPages[0],
            messages: [...newPages[0].messages, optimisticMessage],
          };
          return { ...old, pages: newPages };
        }
      );

      return { previousData, optimisticId };
    },
    onSuccess: (response, variables, context) => {
      const conversationId = variables.conversation_id;
      if (!conversationId) return;

      const realMessage = response.message;

      queryClient.setQueryData(
        messageQueryKeys.conversationMessages(conversationId, { limit: 50 }),
        (old: any) => {
          if (!old) return old;
          const newPages = old.pages.map((page: any, idx: number) => {
            if (idx !== 0) return page;
            return {
              ...page,
              messages: page.messages.map((msg: any) =>
                msg._id === context?.optimisticId ? realMessage : msg
              ),
            };
          });
          return { ...old, pages: newPages };
        }
      );
    },
    onError: (error, variables, context) => {
      const conversationId = variables.conversation_id;
      if (!conversationId) return handleError(error);

      // Instead of completely removing the optimistic message, update it to show error state
      queryClient.setQueryData(
        messageQueryKeys.conversationMessages(conversationId, { limit: 50 }),
        (old: any) => {
          if (!old) return context?.previousData ?? null;
          
          const newPages = old.pages.map((page: any, idx: number) => {
            if (idx !== 0) return page;
            return {
              ...page,
              messages: page.messages.map((msg: any) =>
                msg._id === context?.optimisticId 
                  ? { ...msg, status: 'failed', error: true }
                  : msg
              ),
            };
          });
          return { ...old, pages: newPages };
        }
      );
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