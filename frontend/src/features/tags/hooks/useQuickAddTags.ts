/**
 * useQuickAddTags hook - fetches most frequently used tags for quick selection
 */

import { useQuery } from '@tanstack/react-query';
import { TagSuggestResponse } from '../models/tag';
import { tagsApi } from '../api/tagsApi';

export interface UseQuickAddTagsOptions {
  limit?: number;
  enabled?: boolean;
}

export function useQuickAddTags({
  limit = 7,
  enabled = true,
}: UseQuickAddTagsOptions = {}) {
  return useQuery({
    queryKey: ['tags', 'quick-add', { limit }],
    queryFn: async (): Promise<TagSuggestResponse> => {
      console.log('⚡ [useQuickAddTags] Fetching quick add tags:', { limit, enabled });
      
      const response = await tagsApi.getQuickAddTags(limit);
      
      console.log('📡 [useQuickAddTags] Raw backend response:', response);
      
      // Normalize id field in case backend returns _id
      const normalizedTags = response.suggestions.map((t: any) => ({
        id: (t as any).id ?? (t as any)._id ?? '',
        name: t.name,
        slug: t.slug,
        display_name: t.display_name,
        category: t.category,
        color: t.color,
        usage_count: t.usage_count ?? 0,
      }));
      
      console.log('✅ [useQuickAddTags] Normalized tags:', normalizedTags);
      
      const result = {
        suggestions: normalizedTags,
        total: response.total,
      };
      
      console.log('🎯 [useQuickAddTags] Final result:', result);
      
      return result;
    },
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 15 * 60 * 1000, // 15 minutes
    retry: 1,
  });
}

export default useQuickAddTags;
