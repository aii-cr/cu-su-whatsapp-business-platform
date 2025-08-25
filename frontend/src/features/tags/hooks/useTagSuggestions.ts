/**
 * useTagSuggestions hook - fetches tag suggestions or popular tags
 */

import { useQuery } from '@tanstack/react-query';
import { TagSuggestResponse } from '../models/tag';
import { tagApi } from '../api/tagsApi';

export interface UseTagSuggestionsOptions {
  query: string;
  excludeIds?: string[];
  limit?: number;
  enabled?: boolean;
}

export function useTagSuggestions({
  query,
  excludeIds = [],
  limit = 10,
  enabled = true,
}: UseTagSuggestionsOptions) {
  return useQuery({
    queryKey: ['tags', 'suggestions', { query, excludeIds, limit }],
    queryFn: async (): Promise<TagSuggestResponse> => {
      console.log('🔍 [useTagSuggestions] Fetching suggestions:', { query, excludeIds, limit, enabled });
      
      const response = await tagApi.suggestTags({
        query: query.trim(), // Empty query returns popular tags
        limit,
        exclude_ids: excludeIds,
      });
      
      console.log('📡 [useTagSuggestions] Raw backend response:', response);
      
      // Backend returns 'suggestions' field, normalize to match frontend expectations
      const suggestions = response.suggestions || [];
      
      console.log('📋 [useTagSuggestions] Extracted suggestions:', suggestions);
      
      // Normalize id field in case backend returns _id
      const normalizedTags = suggestions.map((t: any) => ({
        id: (t as any).id ?? (t as any)._id ?? '',
        name: t.name,
        slug: t.slug,
        display_name: t.display_name,
        category: t.category,
        color: t.color,
        usage_count: t.usage_count ?? 0,
      }));
      
      console.log('✅ [useTagSuggestions] Normalized tags:', normalizedTags);
      
      const result = {
        suggestions: normalizedTags,
        total: response.total,
        query: response.query,
        is_popular: response.is_popular,
      };
      
      console.log('🎯 [useTagSuggestions] Final result:', result);
      
      return result;
    },
    enabled,
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });
}

export default useTagSuggestions;
