/**
 * Users API client functions.
 * Handles all user-related API calls to the FastAPI backend.
 */

import { httpClient } from '@/lib/http';
import { User } from '../hooks/useUsers';

export interface UserSearchParams {
  search?: string;
  page?: number;
  per_page?: number;
  is_active?: boolean;
}

export interface UserListResponse {
  users: User[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export class UsersApi {
  /**
   * Search users with filters and pagination
   */
  static async searchUsers(params: UserSearchParams = {}): Promise<UserListResponse> {
    try {
      const searchParams = new URLSearchParams();
      
      // Add search parameters
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });

      const response = await httpClient.get<UserListResponse>(
        `/auth/users/list?${searchParams.toString()}`
      );
      return response;
    } catch (error) {
      throw error;
    }
  }

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
