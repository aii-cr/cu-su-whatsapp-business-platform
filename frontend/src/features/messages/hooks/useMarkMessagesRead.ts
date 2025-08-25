/**
 * Custom hook for marking messages as read.
 * Handles the API call to mark inbound messages as read when agent views them.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { MessagesApi, MarkMessagesReadResponse } from '../api/messagesApi';
import { toast } from '@/components/feedback/Toast';

export function useMarkMessagesRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (conversationId: string): Promise<MarkMessagesReadResponse> => {
      return await MessagesApi.markMessagesRead(conversationId);
    },
    onSuccess: (data, conversationId) => {
      // Invalidate and refetch messages for this conversation
      queryClient.invalidateQueries({
        queryKey: ['messages', conversationId]
      });

      // Invalidate conversation data to update unread counts
      queryClient.invalidateQueries({
        queryKey: ['conversation', conversationId]
      });

      // Invalidate conversations list to update unread counts
      queryClient.invalidateQueries({
        queryKey: ['conversations']
      });

      // Log success (but don't show toast to avoid spam)
      console.log(`✅ Marked ${data.messages_marked_read} messages as read in conversation ${conversationId}`);
    },
    onError: (error, conversationId) => {
      console.error(`❌ Failed to mark messages as read for conversation ${conversationId}:`, error);
      // Don't show error toast to avoid spam - this is a background operation
    }
  });
}

