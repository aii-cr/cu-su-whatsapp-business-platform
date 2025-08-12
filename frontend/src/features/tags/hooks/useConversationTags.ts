/**
 * React hooks for conversation tag assignment operations.
 * Provides TanStack Query integration for assigning/unassigning tags to conversations.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from '@/components/feedback/Toast';
import { 
  ConversationTag,
  ConversationTagAssignRequest,
  ConversationTagUnassignRequest,
  TagDenormalized,
} from '../models/tag';
import { conversationTagsApi, handleTagApiError } from '../api/tagsApi';
import { tagQueryKeys } from './useTags';

// Query keys for conversation tags
export const conversationTagQueryKeys = {
  all: ['conversation-tags'] as const,
  conversationTags: (conversationId: string) => [...conversationTagQueryKeys.all, conversationId] as const,
};

// Hook for getting conversation tags
export function useConversationTags(conversationId: string | undefined) {
  return useQuery({
    queryKey: conversationTagQueryKeys.conversationTags(conversationId || ''),
    queryFn: () => conversationTagsApi.getConversationTags(conversationId!),
    enabled: !!conversationId,
    staleTime: 2 * 60 * 1000, // Consider data fresh for 2 minutes
    retry: (failureCount, error) => {
      // Don't retry on 4xx errors
      const errorMessage = error?.message || '';
      if (errorMessage.includes('400') || errorMessage.includes('401') || errorMessage.includes('403')) {
        return false;
      }
      return failureCount < 3;
    },
  });
}

// Hook for assigning tags to conversations
export function useAssignConversationTags() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ 
      conversationId, 
      assignData 
    }: { 
      conversationId: string; 
      assignData: ConversationTagAssignRequest;
    }) => conversationTagsApi.assignTags(conversationId, assignData),
    onMutate: async ({ conversationId, assignData }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ 
        queryKey: conversationTagQueryKeys.conversationTags(conversationId) 
      });

      // Snapshot the previous value
      const previousTags = queryClient.getQueryData<ConversationTag[]>(
        conversationTagQueryKeys.conversationTags(conversationId)
      );

      // Optimistically add new tags (we don't have full tag data, so we'll wait for the response)
      // This is a placeholder for optimistic updates
      
      return { previousTags, conversationId };
    },
    onSuccess: (newConversationTags, { conversationId }) => {
      // Update the conversation tags cache
      queryClient.setQueryData(
        conversationTagQueryKeys.conversationTags(conversationId),
        (oldTags: ConversationTag[] = []) => {
          // Merge with existing tags, avoiding duplicates
          const existingTagIds = new Set(oldTags.map(t => t.tag.id));
          const newTags = newConversationTags.filter(t => !existingTagIds.has(t.tag.id));
          return [...oldTags, ...newTags];
        }
      );

      // Update tag usage counts in tag caches
      newConversationTags.forEach(convTag => {
        queryClient.setQueryData(
          tagQueryKeys.detail(convTag.tag.id),
          (oldTag: any) => oldTag ? { ...oldTag, usage_count: oldTag.usage_count + 1 } : oldTag
        );
      });

      // Invalidate tag lists to refresh usage counts
      queryClient.invalidateQueries({ queryKey: tagQueryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: tagQueryKeys.suggestions() });

      const tagNames = newConversationTags.map(t => t.tag.name).join(', ');
      const message = newConversationTags.length === 1 
        ? `Assigned tag "${tagNames}"` 
        : `Assigned ${newConversationTags.length} tags`;
      toast.success(message);
    },
    onError: (error, { conversationId }, context) => {
      // Rollback optimistic update
      if (context?.previousTags) {
        queryClient.setQueryData(
          conversationTagQueryKeys.conversationTags(conversationId),
          context.previousTags
        );
      }
      
      const tagError = handleTagApiError(error);
      toast.error(`Failed to assign tags: ${tagError.message}`);
      throw tagError;
    },
  });
}

// Hook for unassigning tags from conversations
export function useUnassignConversationTags() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ 
      conversationId, 
      unassignData 
    }: { 
      conversationId: string; 
      unassignData: ConversationTagUnassignRequest;
    }) => conversationTagsApi.unassignTags(conversationId, unassignData),
    onMutate: async ({ conversationId, unassignData }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ 
        queryKey: conversationTagQueryKeys.conversationTags(conversationId) 
      });

      // Snapshot the previous value
      const previousTags = queryClient.getQueryData<ConversationTag[]>(
        conversationTagQueryKeys.conversationTags(conversationId)
      );

      // Optimistically remove tags
      if (previousTags) {
        const updatedTags = previousTags.filter(
          convTag => !unassignData.tag_ids.includes(convTag.tag.id)
        );
        queryClient.setQueryData(
          conversationTagQueryKeys.conversationTags(conversationId),
          updatedTags
        );
      }

      return { previousTags, conversationId, unassignData };
    },
    onSuccess: (result, { conversationId, unassignData }, context) => {
      // Update tag usage counts in tag caches
      unassignData.tag_ids.forEach(tagId => {
        queryClient.setQueryData(
          tagQueryKeys.detail(tagId),
          (oldTag: any) => oldTag ? { 
            ...oldTag, 
            usage_count: Math.max(0, oldTag.usage_count - 1) 
          } : oldTag
        );
      });

      // Invalidate tag lists to refresh usage counts
      queryClient.invalidateQueries({ queryKey: tagQueryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: tagQueryKeys.suggestions() });

      const count = result.unassigned_count;
      const message = count === 1 
        ? 'Unassigned 1 tag' 
        : `Unassigned ${count} tags`;
      toast.success(message);
    },
    onError: (error, { conversationId }, context) => {
      // Rollback optimistic update
      if (context?.previousTags) {
        queryClient.setQueryData(
          conversationTagQueryKeys.conversationTags(conversationId),
          context.previousTags
        );
      }
      
      const tagError = handleTagApiError(error);
      toast.error(`Failed to unassign tags: ${tagError.message}`);
      throw tagError;
    },
  });
}

// Utility hook for managing conversation tag operations
export function useConversationTagOperations(conversationId: string) {
  const assignMutation = useAssignConversationTags();
  const unassignMutation = useUnassignConversationTags();
  const { data: conversationTags, isLoading, error } = useConversationTags(conversationId);

  const assignTag = async (tagId: string, autoAssigned: boolean = false) => {
    return assignMutation.mutateAsync({
      conversationId,
      assignData: {
        tag_ids: [tagId],
        auto_assigned: autoAssigned,
      },
    });
  };

  const assignTags = async (tagIds: string[], autoAssigned: boolean = false) => {
    return assignMutation.mutateAsync({
      conversationId,
      assignData: {
        tag_ids: tagIds,
        auto_assigned: autoAssigned,
      },
    });
  };

  const unassignTag = async (tagId: string) => {
    return unassignMutation.mutateAsync({
      conversationId,
      unassignData: {
        tag_ids: [tagId],
      },
    });
  };

  const unassignTags = async (tagIds: string[]) => {
    return unassignMutation.mutateAsync({
      conversationId,
      unassignData: {
        tag_ids: tagIds,
      },
    });
  };

  const toggleTag = async (tagId: string) => {
    const isAssigned = conversationTags?.some(ct => ct.tag.id === tagId);
    
    if (isAssigned) {
      return unassignTag(tagId);
    } else {
      return assignTag(tagId);
    }
  };

  const getAssignedTagIds = (): string[] => {
    return conversationTags?.map(ct => ct.tag.id) || [];
  };

  const getAssignedTags = (): TagDenormalized[] => {
    return conversationTags?.map(ct => ct.tag) || [];
  };

  const isTagAssigned = (tagId: string): boolean => {
    return conversationTags?.some(ct => ct.tag.id === tagId) || false;
  };

  return {
    conversationTags,
    isLoading,
    error,
    assignTag,
    assignTags,
    unassignTag,
    unassignTags,
    toggleTag,
    getAssignedTagIds,
    getAssignedTags,
    isTagAssigned,
    isAssigning: assignMutation.isPending,
    isUnassigning: unassignMutation.isPending,
    isOperating: assignMutation.isPending || unassignMutation.isPending,
  };
}

// Hook for invalidating conversation tag caches
export function useInvalidateConversationTags() {
  const queryClient = useQueryClient();

  return {
    invalidateAll: () => {
      queryClient.invalidateQueries({ queryKey: conversationTagQueryKeys.all });
    },
    invalidateConversation: (conversationId: string) => {
      queryClient.invalidateQueries({ 
        queryKey: conversationTagQueryKeys.conversationTags(conversationId) 
      });
    },
  };
}



