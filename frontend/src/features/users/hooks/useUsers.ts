/**
 * React hooks for user management and lookups.
 * Used for displaying agent names in conversations.
 */

import { useQuery } from '@tanstack/react-query';
import { httpClient, createApiErrorHandler } from '@/lib/http';
import { toast } from '@/components/feedback/Toast';

// User interface (matching backend UserResponse)
export interface User {
  _id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  department_id?: string;
  role_ids?: string[];
  is_active?: boolean;
  status?: string;
  last_login?: string;
  created_at?: string;
  updated_at?: string;
  preferences?: Record<string, any>;
}

// Users API
export class UsersApi {
  /**
   * Get user by ID
   */
  static async getUser(userId: string): Promise<User> {
    try {
      const response = await httpClient.get<User>(`/auth/users/${userId}`);
      return response;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Get multiple users by IDs
   */
  static async getUsers(userIds: string[]): Promise<User[]> {
    try {
      const response = await httpClient.post<User[]>('/auth/users/bulk', { user_ids: userIds });
      return response;
    } catch (error) {
      throw error;
    }
  }
}

// Query keys
export const userQueryKeys = {
  all: ['users'] as const,
  user: (id: string) => ['users', id] as const,
  bulk: (ids: string[]) => ['users', 'bulk', ids.sort().join(',')] as const,
};

/**
 * Hook to fetch a single user
 */
export function useUser(userId: string | null | undefined) {
  const handleError = createApiErrorHandler((msg: string) => toast.error(msg));

  return useQuery({
    queryKey: userQueryKeys.user(userId || ''),
    queryFn: () => UsersApi.getUser(userId!),
    enabled: !!userId,
    staleTime: 5 * 60 * 1000,
    retry: (failureCount, error) => {
      if (error && typeof error === 'object' && 'statusCode' in error) {
        const statusCode = (error as { statusCode: number }).statusCode;
        if (statusCode === 404) {
          return false;
        }
      }
      return failureCount < 2;
    },
  });
}

/**
 * Hook to fetch multiple users
 */
export function useUsers(userIds: string[]) {
  const handleError = createApiErrorHandler((msg: string) => toast.error(msg));

  return useQuery({
    queryKey: userQueryKeys.bulk(userIds),
    queryFn: () => UsersApi.getUsers(userIds),
    enabled: userIds.length > 0,
    staleTime: 5 * 60 * 1000,
    retry: (failureCount, error) => {
      if (error && typeof error === 'object' && 'statusCode' in error) {
        const statusCode = (error as { statusCode: number }).statusCode;
        if (statusCode === 404) {
          return false;
        }
      }
      return failureCount < 2;
    },
  });
}

/**
 * Utility function to get user display name
 */
export function getUserDisplayName(user: User | null | undefined): string {
  if (!user) return 'Unknown User';
  
  // Combine first_name and last_name
  const fullName = [user.first_name, user.last_name].filter(Boolean).join(' ').trim();
  return fullName || user.email || 'Unknown User';
}

/**
 * Utility function to get user full name (first + last)
 */
export function getUserFullName(user: User | null | undefined): string {
  if (!user) return '';
  return [user.first_name, user.last_name].filter(Boolean).join(' ').trim();
}