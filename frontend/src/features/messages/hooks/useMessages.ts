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
      
      console.log('🚀 [OPTIMISTIC] Starting optimistic update for conversation:', conversationId);
      
      // Cancel any outgoing refetches (so they don't overwrite our optimistic update)
      await queryClient.cancelQueries({
        queryKey: messageQueryKeys.conversationMessages(conversationId, { limit: 50 }),
      });

      // Snapshot the previous value
      const previousMessages = queryClient.getQueryData(
        messageQueryKeys.conversationMessages(conversationId, { limit: 50 })
      );

      // Create optimistic message
      const optimisticMessage: Message = {
        _id: `optimistic-${Date.now()}-${Math.random()}`,
        conversation_id: conversationId,
        message_type: 'text',
        direction: 'outbound',
        sender_role: 'agent',
        sender_id: user?._id || 'current-user',
        sender_name: user?.first_name || user?.email || 'You',
        text_content: variables.text_content,
        status: 'sending',
        timestamp: new Date().toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        type: 'text',
      } as Message;

      console.log('🚀 [OPTIMISTIC] Created optimistic message:', optimisticMessage._id);

      // Optimistically update the query cache
      queryClient.setQueryData(
        messageQueryKeys.conversationMessages(conversationId, { limit: 50 }),
        (oldData: any) => {
          if (!oldData) {
            console.log('⚠️ [OPTIMISTIC] No existing query data, creating new structure');
            return {
              pages: [{
                messages: [optimisticMessage],
                next_cursor: null,
                has_more: false,
                anchor: 'latest',
                cache_hit: false
              }]
            };
          }
          
          console.log('🚀 [OPTIMISTIC] Updating existing query data');
          const updatedPages = [...oldData.pages];
          if (updatedPages[0]) {
            updatedPages[0] = {
              ...updatedPages[0],
              messages: [...updatedPages[0].messages, optimisticMessage]
            };
          }
          
          return {
            ...oldData,
            pages: updatedPages
          };
        }
      );

      console.log('🚀 [OPTIMISTIC] Added optimistic message to query cache');
      
      // Return a context object with the snapshotted value and optimistic message
      return { previousMessages, optimisticMessage };
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
      
      // Update the optimistic message with real data
      if (context?.optimisticMessage) {
        console.log('✅ [OPTIMISTIC] Updating optimistic message with real data');
        console.log('✅ [OPTIMISTIC] Optimistic ID:', context.optimisticMessage._id);
        console.log('✅ [OPTIMISTIC] Real ID:', sentMessage._id);
        
        queryClient.setQueryData(
          messageQueryKeys.conversationMessages(conversationId, { limit: 50 }),
          (oldData: any) => {
            if (!oldData) return oldData;
            
            const updatedPages = oldData.pages.map((page: any) => ({
              ...page,
              messages: page.messages.map((msg: Message) => {
                if (msg._id === context.optimisticMessage._id) {
                  console.log('✅ [OPTIMISTIC] Replacing optimistic message with real message');
                  return { ...sentMessage, _id: sentMessage._id };
                }
                return msg;
              })
            }));
            
            return {
              ...oldData,
              pages: updatedPages
            };
          }
        );
        
        console.log('✅ [OPTIMISTIC] Updated optimistic message with real data');
      }
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