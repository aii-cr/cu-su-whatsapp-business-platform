/**
 * Authentication API client functions.
 * Handles login, logout, and session validation with the FastAPI backend.
 */

import { httpClient, handleApiError } from '@/lib/http';
import { LoginCredentials, RegisterData, User, AuthResponse } from '@/lib/auth';

export class AuthApi {
  /**
   * Login user with email and password
   */
  static async login(credentials: LoginCredentials): Promise<User> {
    try {
      const response = await httpClient.post<AuthResponse>(
        '/auth/users/login',
        credentials
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }

  /**
   * Logout current user
   */
  static async logout(): Promise<void> {
    try {
      await httpClient.post('/auth/users/logout');
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }

  /**
   * Get current user profile
   */
  static async getCurrentUser(): Promise<User> {
    try {
      const response = await httpClient.get<User>('/auth/users/me');
      return response;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }

  /**
   * Register a new user (admin only)
   */
  static async register(userData: RegisterData): Promise<User> {
    try {
      const response = await httpClient.post<AuthResponse>(
        '/auth/users/register',
        userData
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }

  /**
   * Refresh user session
   */
  static async refreshSession(): Promise<User> {
    try {
      const response = await httpClient.post<User>('/auth/users/refresh');
      return response;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }
}