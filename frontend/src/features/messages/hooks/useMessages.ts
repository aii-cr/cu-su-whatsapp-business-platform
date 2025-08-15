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
 * Hook to fetch messages for a conversation with infinite scroll
 */
export function useMessages(conversationId: string, limit: number = 50) {
  const handleError = createApiErrorHandler((msg: string) => toast.error(msg));

  const query = useInfiniteQuery<MessageListResponse>({
    queryKey: messageQueryKeys.conversationMessages(conversationId, { limit }),
    queryFn: async ({ pageParam = 0 }) => {
      return MessagesApi.getMessages(
        conversationId,
        pageParam as number, // offset
        limit
      );
    },
    getNextPageParam: (lastPage, allPages) => {
      const nextOffset = allPages.length * limit;
      return nextOffset < lastPage.total ? nextOffset : undefined;
    },
    staleTime: 30 * 1000, // 30 seconds
    enabled: !!conversationId,
    initialPageParam: 0,
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
        sender_name: user?.name || 
                    (user?.first_name && user?.last_name ? `${user.first_name} ${user.last_name}` : null) ||
                    user?.email || 'You',
        text_content: variables.text_content,
        status: 'sending', // Show as sending with loading indicator (pending state)
        timestamp: new Date().toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        type: 'text',
        whatsapp_message_id: undefined,
        whatsapp_data: undefined,
        isOptimistic: true, // Mark as optimistic to handle real-time updates
      };

      // Get current data for rollback
      const previousMessages = queryClient.getQueryData(
        messageQueryKeys.conversationMessages(conversationId, { limit: 50 })
      );

      // Optimistically add the message
      console.log('🔄 [OPTIMISTIC] Adding optimistic message to query:', messageQueryKeys.conversationMessages(conversationId, { limit: 50 }));
      queryClient.setQueryData(
        messageQueryKeys.conversationMessages(conversationId, { limit: 50 }),
        (old: unknown) => {
          if (!old || typeof old !== 'object') return old;
          const oldData = old as { pages: { messages: Message[], total: number }[] };
          
          // Add the optimistic message to the end of the first page (newest messages)
          const newPages = [...oldData.pages];
          if (newPages[0]) {
            newPages[0] = {
              ...newPages[0],
              messages: [...newPages[0].messages, optimisticMessage],
              total: newPages[0].total + 1
            };
          }
          
          return {
            ...oldData,
            pages: newPages
          };
        }
      );

      console.log('✅ [OPTIMISTIC] Optimistic message added successfully:', optimisticMessage._id);
      return { previousMessages, optimisticMessage };
    },
    onSuccess: (response, variables, context) => {
      const conversationId = variables.conversation_id;
      const sentMessage = response.message; // The actual message object is nested in the response
      
      if (!conversationId) {
        console.error('No conversation ID available in success callback');
        return;
      }
      
      // Update optimistic message with real backend data
      queryClient.setQueryData(
        messageQueryKeys.conversationMessages(conversationId, { limit: 50 }),
        (old: unknown) => {
          if (!old || typeof old !== 'object' || !context?.optimisticMessage) return old;
          const oldData = old as { pages: { messages: Message[], total: number }[] };
          
          const newPages = [...oldData.pages];
          if (newPages[0]) {
            const messageIndex = newPages[0].messages.findIndex(
              (msg: Message) => msg._id === context.optimisticMessage._id
            );
            
            if (messageIndex !== -1) {
              // Replace optimistic message with real backend data
              newPages[0].messages[messageIndex] = {
                ...sentMessage,
                _id: sentMessage._id, // Use backend ID
                status: 'sent', // Mark as sent (single check mark)
                isOptimistic: false // No longer optimistic since it's real data
              };
              
              console.log('✅ [MESSAGE] Replaced optimistic message with real data:', sentMessage._id);
            }
          }
          
          return {
            ...oldData,
            pages: newPages
          };
        }
      );

      console.log('✅ [MESSAGE] Sent successfully, updated to "sent" status');
      toast.success('Message sent');
    },
    onError: (error, variables, context) => {
      const conversationId = variables.conversation_id;
      
      if (!conversationId) {
        handleError(error);
        return;
      }
      
      // Remove the optimistic message since sending failed
      queryClient.setQueryData(
        messageQueryKeys.conversationMessages(conversationId, { limit: 50 }),
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