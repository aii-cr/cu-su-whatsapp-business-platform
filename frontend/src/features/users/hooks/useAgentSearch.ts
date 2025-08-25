/**
 * React hook for searching agents with debounced search functionality.
 * Used for the assigned agent filter in conversations.
 */

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useDebounce } from '@/hooks/useDebounce';
import { UsersApi, UserSearchParams } from '../api/usersApi';
import { User } from './useUsers';
import { createApiErrorHandler } from '@/lib/http';
import { toast } from '@/components/feedback/Toast';

// Query keys for agent search
export const agentSearchQueryKeys = {
  search: (params: UserSearchParams) => ['agents', 'search', params] as const,
};

/**
 * Hook to search agents with debounced search
 */
export function useAgentSearch(searchTerm: string, limit: number = 5) {
  const debouncedSearchTerm = useDebounce(searchTerm, 300); // 300ms debounce
  
  const searchParams = useMemo(() => ({
    search: debouncedSearchTerm,
    per_page: limit,
    is_active: true, // Only show active agents
  }), [debouncedSearchTerm, limit]);

  const handleError = createApiErrorHandler((msg: string) => {
    // Don't show toast for search errors, just log them
    console.error('Agent search error:', msg);
  });

  return useQuery({
    queryKey: agentSearchQueryKeys.search(searchParams),
    queryFn: () => UsersApi.searchUsers(searchParams),
    enabled: debouncedSearchTerm.length >= 2, // Only search when 2+ characters
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: false, // Don't retry search queries
    onError: handleError,
  });
}

/**
 * Hook to get agent display options for select dropdown
 */
export function useAgentOptions(searchTerm: string) {
  const { data, isLoading, error } = useAgentSearch(searchTerm);
  
  const options = useMemo(() => {
    if (!data?.users) return [];
    
    return data.users.map((user: User) => ({
      value: user._id,
      label: `${user.first_name} ${user.last_name}`.trim() || user.email,
      email: user.email,
      user,
    }));
  }, [data?.users]);

  return {
    options,
    isLoading,
    error,
    hasResults: options.length > 0,
  };
}
