/**
 * HTTP client for API communication with the FastAPI backend.
 * Handles authentication via session cookies and provides consistent error handling.
 */

import { getApiUrl } from './config';

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
      // Add timeout for requests
      signal: AbortSignal.timeout(30000), // 30 second timeout
    };

    try {
      const response = await fetch(url, config);
      
      // Check if response is JSON
      const contentType = response.headers.get('content-type');
      let data: ApiResponse<T>;
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        // Handle non-JSON responses (like 404 HTML pages)
        const text = await response.text();
        throw new ApiError(
          response.status,
          `HTTP_${response.status}`,
          `Server returned ${response.status}: ${text.substring(0, 100)}`,
          { response_text: text }
        );
      }

      if (!response.ok) {
        // Handle authentication/authorization failures
        if (response.status === 401 || response.status === 403) {
          // Mark session expired so the login page can show a toast, but do not hard-redirect here.
          // Global redirects from the HTTP layer can cause reload loops if already on /login.
          try {
            if (typeof window !== 'undefined') {
              sessionStorage.setItem('sessionExpired', '1');
            }
          } catch {}
        }

        throw new ApiError(
          response.status,
          (data as any).error_code || `HTTP_${response.status}`,
          (data as any).error_message || (data as any).message || 'Request failed',
          (data as any).details,
          (data as any).request_id
        );
      }

      return (data.data || data) as T;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }

      // Check if it's a timeout error
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ApiError(
          408,
          'REQUEST_TIMEOUT',
          'Request timed out. Please try again.',
          error
        );
      }

      // Network or other errors
      console.error('Network error:', error);
      throw new ApiError(
        500,
        'NETWORK_ERROR',
        'Unable to connect to the server. Please check your internet connection and try again.',
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
 * Simple error handler that logs errors without notifications
 * Use this for API calls where you don't need user notifications
 */
export const handleApiError = (error: unknown): void => {
  if (error instanceof ApiError) {
    console.error('API Error:', {
      statusCode: error.statusCode,
      errorCode: error.errorCode,
      userMessage: error.userMessage,
      details: error.details,
      requestId: error.requestId
    });
  } else {
    console.error('Unexpected error:', error);
  }
};

/**
 * Handle API errors with user-friendly notifications
 * This function should be used with the notification system from components
 */
export const createApiErrorHandler = (showError: (message: string, id?: string) => void) => {
  return (error: unknown): void => {
    if (error instanceof ApiError) {
      // Create a unique ID for this error to prevent duplicates
      const errorId = `${error.errorCode}-${error.statusCode}`;
      
      // Handle specific error codes from backend
      switch (error.errorCode) {
        case 'AUTH_1001':
          showError('Invalid email or password. Please check your credentials and try again.', errorId);
          break;
        case 'AUTH_1002':
          showError('Your session has expired. Please log in again.', errorId);
          break;
        case 'USER_1101':
          showError('User information could not be found. Please refresh the page.', errorId);
          break;
        case 'CONV_2101':
          showError('Conversation not found. It may have been deleted or moved.', errorId);
          break;
        case 'MSG_2106':
          showError('Failed to send message. Please try again.', errorId);
          break;
        case 'NETWORK_ERROR':
          showError('Network connection failed. Please check your internet connection and try again.', errorId);
          break;
        case 'REQUEST_TIMEOUT':
          showError('Request timed out. Please try again.', errorId);
          break;
        case 'HTTP_404':
          showError('The requested resource was not found. Please check the URL and try again.', errorId);
          break;
        case 'HTTP_403':
          showError('You do not have permission to access this resource.', errorId);
          break;
        case 'HTTP_500':
          showError('Server error occurred. Please try again later.', errorId);
          break;
        case 'HTTP_503':
          showError('Service temporarily unavailable. Please try again later.', errorId);
          break;
        default:
          // Check if it's a generic HTTP error
          if (error.errorCode.startsWith('HTTP_')) {
            showError(`Server error (${error.statusCode}). Please try again.`, errorId);
          } else {
            showError(error.userMessage || 'An unexpected error occurred. Please try again.', errorId);
          }
      }
    } else {
      showError('An unexpected error occurred. Please try again.');
    }
    
    console.error('API Error:', error);
  };
};