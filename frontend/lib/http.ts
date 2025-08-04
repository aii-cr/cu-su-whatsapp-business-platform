/**
 * HTTP client for API communication with the FastAPI backend.
 * Handles authentication via session cookies and provides consistent error handling.
 */

import { getApiUrl } from './config';
import { toast } from 'react-hot-toast';

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  message?: string;
  error_code?: string;
  error_message?: string;
  details?: unknown;
  request_id?: string;
}

export class ApiError extends Error {
  constructor(
    public statusCode: number,
    public errorCode: string,
    public userMessage: string,
    public details?: unknown,
    public requestId?: string
  ) {
    super(userMessage);
    this.name = 'ApiError';
  }
}

export class HttpClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = getApiUrl(''); // This will return: http://localhost:8000/api/v1
  }

  /**
   * Make an HTTP request to the API
   */
  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      ...options,
      credentials: 'include', // Essential for session cookies
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      const data: ApiResponse<T> = await response.json();

      if (!response.ok) {
        // Handle authentication errors
        if (response.status === 401) {
          // Redirect to login on authentication failure
          if (typeof window !== 'undefined') {
            window.location.href = '/login';
          }
        }

        throw new ApiError(
          response.status,
          data.error_code || `HTTP_${response.status}`,
          data.error_message || data.message || 'Request failed',
          data.details,
          data.request_id
        );
      }

      return (data.data || data) as T;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }

      // Network or other errors
      throw new ApiError(
        500,
        'NETWORK_ERROR',
        'Network error occurred. Please check your connection.',
        error
      );
    }
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  /**
   * POST request
   */
  async post<T>(endpoint: string, data?: unknown, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * PUT request
   */
  async put<T>(endpoint: string, data?: unknown, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }
}

// Export singleton instance
export const httpClient = new HttpClient();

/**
 * Handle API errors with user-friendly notifications
 */
export const handleApiError = (error: unknown): void => {
  if (error instanceof ApiError) {
    // Handle specific error codes from backend
    switch (error.errorCode) {
      case 'AUTH_1001':
        toast.error('Invalid email or password');
        break;
      case 'AUTH_1002':
        toast.error('Session expired. Please login again.');
        break;
      case 'USER_1101':
        toast.error('User not found');
        break;
      case 'CONV_2101':
        toast.error('Conversation not found');
        break;
      case 'MSG_2106':
        toast.error('Failed to send message');
        break;
      case 'NETWORK_ERROR':
        toast.error('Network connection failed. Please try again.');
        break;
      default:
        toast.error(error.userMessage || 'An error occurred');
    }
  } else {
    toast.error('An unexpected error occurred');
  }
  
  console.error('API Error:', error);
};