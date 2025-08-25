/**
 * usePopularTags hook - fetches popular/recent tags for quick selection
 */

import { useQuery } from '@tanstack/react-query';
import { TagSummary } from '../models/tag';
import { tagApi } from '../api/tagsApi';

export interface UsePopularTagsOptions {
  limit?: number;
  enabled?: boolean;
}

export function usePopularTags({
  limit = 8,
  enabled = true,
}: UsePopularTagsOptions = {}) {
  return useQuery({
    queryKey: ['tags', 'popular', { limit }],
    queryFn: async (): Promise<TagSummary[]> => {
      const response = await tagApi.listTags({
        limit,
        sort_by: 'usage_count',
        sort_order: 'desc',
        status: 'active',
      });
      
      // Convert to TagSummary format - backend already provides correct structure
      return response.tags.map(tag => ({
        id: tag.id,
        name: tag.name,
        slug: tag.slug,
        display_name: tag.display_name,
        category: tag.category,
        color: tag.color,
        usage_count: tag.usage_count,
      }));
    },
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 15 * 60 * 1000, // 15 minutes
  });
}

export default usePopularTags;

