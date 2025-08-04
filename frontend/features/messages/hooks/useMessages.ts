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
import { useNotifications } from '@/components/feedback/NotificationSystem';
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
 * Hook to fetch messages for a conversation with infinite scroll
 */
export function useMessages(conversationId: string, limit: number = 50) {
  const { showError } = useNotifications();
  const handleError = createApiErrorHandler(showError);

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
    onError: handleError,
  });
}

/**
 * Hook to send a message with optimistic updates
 */
export function useSendMessage() {
  const queryClient = useQueryClient();
  const { showSuccess, showError } = useNotifications();
  const handleError = createApiErrorHandler(showError);
  const { user } = useAuthStore();

  return useMutation({
    mutationFn: (data: SendMessageRequest) => MessagesApi.sendMessage(data),
    onMutate: async (variables) => {
      const conversationId = variables.conversation_id;
      
      // Don't cancel queries - let WebSocket updates work normally
      // Just create an optimistic message and add it
      
      // Create optimistic message with unique temp ID
      const optimisticId = `temp-${Date.now()}-${Math.random()}`;
      const optimisticMessage: Message & { isOptimistic?: boolean } = {
        _id: optimisticId,
        conversation_id: conversationId,
        message_type: 'text',
        direction: 'outbound',
        sender_role: 'agent',
        sender_id: user?._id || '',
        sender_name: user?.name || user?.email || 'You',
        text_content: variables.text_content,
        status: 'sending', // Show as sending with loading indicator
        timestamp: new Date().toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        type: 'text',
        whatsapp_message_id: null,
        whatsapp_data: null,
        isOptimistic: true, // Mark as optimistic
      };

      // Get current data for rollback
      const previousMessages = queryClient.getQueryData(
        messageQueryKeys.conversationMessages(conversationId)
      );

      // Optimistically add the message
      queryClient.setQueryData(
        messageQueryKeys.conversationMessages(conversationId),
        (old: unknown) => {
          if (!old || typeof old !== 'object') return old;
          const oldData = old as { pages: { messages: Message[], total: number }[] };
          
          // Add the optimistic message to the first page
          const newPages = [...oldData.pages];
          if (newPages[0]) {
            newPages[0] = {
              ...newPages[0],
              messages: [optimisticMessage, ...newPages[0].messages],
              total: newPages[0].total + 1
            };
          }
          
          return {
            ...oldData,
            pages: newPages
          };
        }
      );

      return { previousMessages, optimisticMessage };
    },
    onSuccess: (response, variables, context) => {
      const conversationId = variables.conversation_id || response.conversation_id;
      
      // Update optimistic message status to "sent" - keep the message in UI
      queryClient.setQueryData(
        messageQueryKeys.conversationMessages(conversationId),
        (old: unknown) => {
          if (!old || typeof old !== 'object' || !context?.optimisticMessage) return old;
          const oldData = old as { pages: { messages: Message[], total: number }[] };
          
          const newPages = [...oldData.pages];
          if (newPages[0]) {
            const messageIndex = newPages[0].messages.findIndex(
              (msg: Message) => msg._id === context.optimisticMessage._id
            );
            
            if (messageIndex !== -1) {
              // Update optimistic message with backend response and "sent" status
              newPages[0].messages[messageIndex] = {
                ...response, // Use real backend data
                _id: context.optimisticMessage._id, // Keep temp ID to avoid duplicates
                status: 'sent', // Mark as sent (single check mark)
                isOptimistic: true // Mark as optimistic to handle WebSocket updates
              };
            }
          }
          
          return {
            ...oldData,
            pages: newPages
          };
        }
      );

      console.log('✅ [MESSAGE] Sent successfully, updated to "sent" status');
    },
    onError: (error, variables, context) => {
      const conversationId = variables.conversation_id;
      
      // Remove the optimistic message since sending failed
      queryClient.setQueryData(
        messageQueryKeys.conversationMessages(conversationId),
        (old: unknown) => {
          if (!old || typeof old !== 'object' || !context?.optimisticMessage) return old;
          const oldData = old as { pages: { messages: Message[], total: number }[] };
          
          const newPages = [...oldData.pages];
          if (newPages[0]) {
            newPages[0] = {
              ...newPages[0],
              messages: newPages[0].messages.filter(
                (msg: Message) => msg._id !== context.optimisticMessage._id
              ),
              total: Math.max(0, newPages[0].total - 1)
            };
          }
          
          return {
            ...oldData,
            pages: newPages
          };
        }
      );
      
      handleError(error);
    },
  });
}

/**
 * Hook to send media message (placeholder)
 */
export function useSendMediaMessage() {
  const queryClient = useQueryClient();
  const { showSuccess, showError } = useNotifications();
  const handleError = createApiErrorHandler(showError);

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

      showSuccess('Media message sent successfully');
    },
    onError: handleError,
  });
}

/**
 * Hook to get message templates
 */
export function useMessageTemplates() {
  const { showError } = useNotifications();
  const handleError = createApiErrorHandler(showError);

  return useQuery({
    queryKey: ['messages', 'templates'],
    queryFn: () => MessagesApi.getTemplates(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    onError: handleError,
  });
}