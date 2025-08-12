/**
 * React hooks for tag management operations.
 * Provides TanStack Query integration for tag CRUD operations with caching and optimistic updates.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from '@/components/feedback/Toast';
import { 
  Tag,
  TagCreate,
  TagUpdate,
  TagListRequest,
  TagListResponse,
  TagSuggestRequest,
  TagSuggestResponse,
} from '../models/tag';
import { tagApi, handleTagApiError } from '../api/tagsApi';

// Query keys for cache management
export const tagQueryKeys = {
  all: ['tags'] as const,
  lists: () => [...tagQueryKeys.all, 'list'] as const,
  list: (params: Partial<TagListRequest>) => [...tagQueryKeys.lists(), params] as const,
  details: () => [...tagQueryKeys.all, 'detail'] as const,
  detail: (id: string) => [...tagQueryKeys.details(), id] as const,
  suggestions: () => [...tagQueryKeys.all, 'suggestions'] as const,
  suggestion: (params: TagSuggestRequest) => [...tagQueryKeys.suggestions(), params] as const,
};

// Hook for listing tags with filtering and pagination
export function useTags(params: Partial<TagListRequest> = {}) {
  return useQuery({
    queryKey: tagQueryKeys.list(params),
    queryFn: () => tagApi.listTags(params),
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
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

// Hook for getting a specific tag
export function useTag(tagId: string | undefined) {
  return useQuery({
    queryKey: tagQueryKeys.detail(tagId || ''),
    queryFn: () => tagApi.getTag(tagId!),
    enabled: !!tagId,
    staleTime: 10 * 60 * 1000, // Consider data fresh for 10 minutes
  });
}

// Hook for tag suggestions (autocomplete)
export function useTagSuggestions(params: TagSuggestRequest, enabled: boolean = true) {
  return useQuery({
    queryKey: tagQueryKeys.suggestion(params),
    queryFn: () => tagApi.suggestTags(params),
    enabled: enabled && params.query.length > 0,
    staleTime: 2 * 60 * 1000, // Consider suggestions fresh for 2 minutes
    retry: false, // Don't retry suggestions automatically
  });
}

// Hook for creating tags
export function useCreateTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (tagData: TagCreate) => tagApi.createTag(tagData),
    onSuccess: (newTag) => {
      // Invalidate and refetch tag lists
      queryClient.invalidateQueries({ queryKey: tagQueryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: tagQueryKeys.suggestions() });
      
      // Add the new tag to the cache
      queryClient.setQueryData(tagQueryKeys.detail(newTag.id), newTag);
      
      toast.success(`Created tag "${newTag.name}"`);
    },
    onError: (error) => {
      const tagError = handleTagApiError(error);
      toast.error(`Failed to create tag: ${tagError.message}`);
      throw tagError;
    },
  });
}

// Hook for updating tags
export function useUpdateTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tagId, tagData }: { tagId: string; tagData: TagUpdate }) => 
      tagApi.updateTag(tagId, tagData),
    onMutate: async ({ tagId, tagData }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: tagQueryKeys.detail(tagId) });

      // Snapshot the previous value
      const previousTag = queryClient.getQueryData<Tag>(tagQueryKeys.detail(tagId));

      // Optimistically update to the new value
      if (previousTag) {
        const optimisticTag = { ...previousTag, ...tagData, updated_at: new Date().toISOString() };
        queryClient.setQueryData(tagQueryKeys.detail(tagId), optimisticTag);
      }

      return { previousTag };
    },
    onSuccess: (updatedTag, { tagId }) => {
      // Update the specific tag in cache
      queryClient.setQueryData(tagQueryKeys.detail(tagId), updatedTag);
      
      // Invalidate lists to ensure consistency
      queryClient.invalidateQueries({ queryKey: tagQueryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: tagQueryKeys.suggestions() });
      
      toast.success(`Updated tag "${updatedTag.name}"`);
    },
    onError: (error, { tagId }, context) => {
      // Rollback optimistic update
      if (context?.previousTag) {
        queryClient.setQueryData(tagQueryKeys.detail(tagId), context.previousTag);
      }
      
      const tagError = handleTagApiError(error);
      toast.error(`Failed to update tag: ${tagError.message}`);
      throw tagError;
    },
  });
}

// Hook for deleting tags
export function useDeleteTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (tagId: string) => tagApi.deleteTag(tagId),
    onMutate: async (tagId) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: tagQueryKeys.detail(tagId) });

      // Snapshot the previous value
      const previousTag = queryClient.getQueryData<Tag>(tagQueryKeys.detail(tagId));

      // Optimistically remove from cache
      queryClient.removeQueries({ queryKey: tagQueryKeys.detail(tagId) });

      return { previousTag, tagId };
    },
    onSuccess: (_, tagId, context) => {
      // Invalidate lists to ensure consistency
      queryClient.invalidateQueries({ queryKey: tagQueryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: tagQueryKeys.suggestions() });
      
      const tagName = context?.previousTag?.name || 'Tag';
      toast.success(`Deleted tag "${tagName}"`);
    },
    onError: (error, tagId, context) => {
      // Rollback optimistic update
      if (context?.previousTag) {
        queryClient.setQueryData(tagQueryKeys.detail(tagId), context.previousTag);
      }
      
      const tagError = handleTagApiError(error);
      toast.error(`Failed to delete tag: ${tagError.message}`);
      throw tagError;
    },
  });
}

// Utility hook for invalidating tag caches
export function useInvalidateTags() {
  const queryClient = useQueryClient();

  return {
    invalidateAll: () => {
      queryClient.invalidateQueries({ queryKey: tagQueryKeys.all });
    },
    invalidateLists: () => {
      queryClient.invalidateQueries({ queryKey: tagQueryKeys.lists() });
    },
    invalidateSuggestions: () => {
      queryClient.invalidateQueries({ queryKey: tagQueryKeys.suggestions() });
    },
    invalidateTag: (tagId: string) => {
      queryClient.invalidateQueries({ queryKey: tagQueryKeys.detail(tagId) });
    },
  };
}

// Hook for prefetching tags
export function usePrefetchTags() {
  const queryClient = useQueryClient();

  return {
    prefetchTags: (params: Partial<TagListRequest> = {}) => {
      queryClient.prefetchQuery({
        queryKey: tagQueryKeys.list(params),
        queryFn: () => tagApi.listTags(params),
        staleTime: 5 * 60 * 1000,
      });
    },
    prefetchTag: (tagId: string) => {
      queryClient.prefetchQuery({
        queryKey: tagQueryKeys.detail(tagId),
        queryFn: () => tagApi.getTag(tagId),
        staleTime: 10 * 60 * 1000,
      });
    },
  };
}



