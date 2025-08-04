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
      
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({
        queryKey: messageQueryKeys.conversation(conversationId)
      });

      // Snapshot the previous value
      const previousMessages = queryClient.getQueryData(
        messageQueryKeys.conversationMessages(conversationId)
      );

      // Create optimistic message
      const optimisticMessage: Message = {
        _id: `temp-${Date.now()}`, // Temporary ID
        conversation_id: conversationId,
        message_type: 'text',
        direction: 'outbound',
        sender_role: 'agent',
        sender_id: user?._id || '',
        sender_name: user?.name || user?.email || 'You',
        text_content: variables.text_content,
        status: 'pending', // Show as pending
        timestamp: new Date().toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        type: 'text',
        whatsapp_message_id: null,
        whatsapp_data: null,
      };

      // Optimistically update to the new value
      queryClient.setQueryData(
        messageQueryKeys.conversationMessages(conversationId),
        (old: any) => {
          if (!old) return old;
          
          // Add the optimistic message to the first page
          const newPages = [...old.pages];
          if (newPages[0]) {
            newPages[0] = {
              ...newPages[0],
              messages: [optimisticMessage, ...newPages[0].messages],
              total: newPages[0].total + 1
            };
          }
          
          return {
            ...old,
            pages: newPages
          };
        }
      );

      return { previousMessages, optimisticMessage };
    },
    onSuccess: (response, variables, context) => {
      const conversationId = variables.conversation_id || response.conversation_id;
      
      // Update the optimistic message with the real response
      queryClient.setQueryData(
        messageQueryKeys.conversationMessages(conversationId),
        (old: any) => {
          if (!old || !context?.optimisticMessage) return old;
          
          const newPages = [...old.pages];
          if (newPages[0]) {
            const messageIndex = newPages[0].messages.findIndex(
              (msg: Message) => msg._id === context.optimisticMessage._id
            );
            
            if (messageIndex !== -1) {
              // Replace optimistic message with real message
              newPages[0].messages[messageIndex] = {
                ...response,
                status: 'sent' // Mark as sent
              };
            }
          }
          
          return {
            ...old,
            pages: newPages
          };
        }
      );

      showSuccess('Message sent successfully');
    },
    onError: (error, variables, context) => {
      const conversationId = variables.conversation_id;
      
      // Revert the optimistic update
      if (context?.previousMessages) {
        queryClient.setQueryData(
          messageQueryKeys.conversationMessages(conversationId),
          context.previousMessages
        );
      } else {
        // If no previous data, just remove the optimistic message
        queryClient.setQueryData(
          messageQueryKeys.conversationMessages(conversationId),
          (old: any) => {
            if (!old || !context?.optimisticMessage) return old;
            
            const newPages = [...old.pages];
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
              ...old,
              pages: newPages
            };
          }
        );
      }
      
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