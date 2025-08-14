/**
 * API client for tag management operations.
 * Handles all HTTP requests to the tags backend endpoints.
 */

import { 
  Tag,
  TagCreate,
  TagUpdate,
  TagListRequest,
  TagListResponse,
  TagSuggestRequest,
  TagSuggestResponse,
  ConversationTag,
  ConversationTagAssignRequest,
  ConversationTagUnassignRequest,
} from '../models/tag';

// API base configuration
import { getApiUrl } from '@/lib/config';

const TAGS_BASE = getApiUrl('tags');
const CONVERSATIONS_BASE = getApiUrl('conversations');

// HTTP client with error handling
class ApiClient {
  private async request<T>(
    url: string,
    options: RequestInit = {}
  ): Promise<T> {
    const defaultHeaders: HeadersInit = {
      'Content-Type': 'application/json',
    };

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
      credentials: 'include', // Include cookies for authentication
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.message || 
          errorData.detail || 
          `HTTP ${response.status}: ${response.statusText}`
        );
      }

      // Handle empty responses (204 No Content)
      if (response.status === 204) {
        return {} as T;
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unexpected error occurred');
    }
  }

  async get<T>(url: string, params?: Record<string, string | number | boolean>): Promise<T> {
    const urlParams = params ? new URLSearchParams(
      Object.entries(params).map(([key, value]) => [key, String(value)])
    ) : '';
    const fullUrl = urlParams ? `${url}?${urlParams}` : url;
    
    return this.request<T>(fullUrl, { method: 'GET' });
  }

  async post<T>(url: string, data?: unknown): Promise<T> {
    return this.request<T>(url, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(url: string, data?: unknown): Promise<T> {
    return this.request<T>(url, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(url: string, data?: unknown): Promise<T> {
    return this.request<T>(url, {
      method: 'DELETE',
      body: data ? JSON.stringify(data) : undefined,
    });
  }
}

const apiClient = new ApiClient();

// Tag management API
export const tagsApi = {
  /**
   * List tags with filtering and pagination
   */
  async listTags(params: Partial<TagListRequest> = {}): Promise<TagListResponse> {
    return apiClient.get<TagListResponse>(`${TAGS_BASE}/`, params);
  },

  /**
   * Get a specific tag by ID
   */
  async getTag(tagId: string): Promise<Tag> {
    return apiClient.get<Tag>(`${TAGS_BASE}/${tagId}`);
  },

  /**
   * Create a new tag
   */
  async createTag(tagData: TagCreate): Promise<Tag> {
    return apiClient.post<Tag>(`${TAGS_BASE}/`, tagData);
  },

  /**
   * Update an existing tag
   */
  async updateTag(tagId: string, tagData: TagUpdate): Promise<Tag> {
    return apiClient.put<Tag>(`${TAGS_BASE}/${tagId}`, tagData);
  },

  /**
   * Delete a tag (soft delete)
   */
  async deleteTag(tagId: string): Promise<void> {
    await apiClient.delete<void>(`${TAGS_BASE}/${tagId}`);
  },

  /**
   * Suggest tags for autocomplete
   */
  async suggestTags(params: TagSuggestRequest): Promise<TagSuggestResponse> {
    const queryParams: Record<string, string | number> = {
      q: params.query,
      limit: params.limit,
    };
    
    if (params.category) {
      queryParams.category = params.category;
    }
    
    if (params.exclude_ids && params.exclude_ids.length > 0) {
      queryParams.exclude_ids = params.exclude_ids.join(',');
    }
    
    return apiClient.get<TagSuggestResponse>(`${TAGS_BASE}/suggest`, queryParams);
  },
  /**
   * Fetch tag-related settings from backend (e.g., max tags per conversation)
   */
  async getSettings(): Promise<{ max_tags_per_conversation: number }> {
    return apiClient.get<{ max_tags_per_conversation: number }>(`${TAGS_BASE}/settings`);
  },
};

// Conversation tag API
export const conversationTagsApi = {
  /**
   * Get all tags assigned to a conversation
   */
  async getConversationTags(conversationId: string): Promise<ConversationTag[]> {
    return apiClient.get<ConversationTag[]>(`${CONVERSATIONS_BASE}/${conversationId}/tags`);
  },

  /**
   * Assign tags to a conversation
   */
  async assignTags(
    conversationId: string, 
    assignData: ConversationTagAssignRequest
  ): Promise<ConversationTag[]> {
    return apiClient.post<ConversationTag[]>(
      `${CONVERSATIONS_BASE}/${conversationId}/tags`,
      assignData
    );
  },

  /**
   * Unassign tags from a conversation
   */
  async unassignTags(
    conversationId: string,
    unassignData: ConversationTagUnassignRequest
  ): Promise<{ message: string; unassigned_count: number }> {
    return apiClient.delete<{ message: string; unassigned_count: number }>(
      `${CONVERSATIONS_BASE}/${conversationId}/tags`,
      unassignData
    );
  },
};

// Export combined API
export const tagApi = {
  ...tagsApi,
  conversations: conversationTagsApi,
};

// Error types for better error handling
export class TagApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string
  ) {
    super(message);
    this.name = 'TagApiError';
  }
}

export class TagValidationError extends TagApiError {
  constructor(message: string, public field?: string) {
    super(message, 422, 'VALIDATION_ERROR');
    this.name = 'TagValidationError';
  }
}

export class TagNotFoundError extends TagApiError {
  constructor(tagId?: string) {
    super(tagId ? `Tag with ID ${tagId} not found` : 'Tag not found', 404, 'TAG_NOT_FOUND');
    this.name = 'TagNotFoundError';
  }
}

export class TagConflictError extends TagApiError {
  constructor(message: string = 'Tag already exists') {
    super(message, 409, 'TAG_ALREADY_EXISTS');
    this.name = 'TagConflictError';
  }
}

// Utility function to handle API errors
export function handleTagApiError(error: unknown): TagApiError {
  if (error instanceof TagApiError) {
    return error;
  }

  if (error instanceof Error) {
    // Try to parse structured error responses
    try {
      const errorMessage = error.message;
      if (errorMessage.includes('422')) {
        return new TagValidationError(errorMessage);
      }
      if (errorMessage.includes('404')) {
        return new TagNotFoundError();
      }
      if (errorMessage.includes('409')) {
        return new TagConflictError(errorMessage);
      }
    } catch {
      // Fall through to generic error
    }

    return new TagApiError(error.message);
  }

  return new TagApiError('An unexpected error occurred');
}



