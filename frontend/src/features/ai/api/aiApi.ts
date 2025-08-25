/**
 * AI API client functions.
 * Handles all AI-related API calls to the FastAPI backend.
 */

import { httpClient } from '@/lib/http';

export interface ConversationContextData {
  conversation_id: string;
  history: Array<{
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    message_id: string;
  }>;
  summary: string;
  session_data: Record<string, any>;
  last_activity?: string;
  memory_size: number;
}

export interface MemoryStatistics {
  active_conversations: number;
  total_sessions: number;
  memory_usage: Record<string, number>;
  last_activity: Record<string, string>;
}

export interface MemoryHealth {
  memory_service: MemoryStatistics;
  status: string;
}

export interface ApiResponse<T> {
  success: boolean;
  conversation_id?: string;
  context?: T;
  statistics?: T;
  memory_service?: T;
  status?: string;
  error?: string;
  message?: string;
}

export class AiApi {
  /**
   * Get conversation context and memory information
   */
  static async getConversationContext(conversationId: string): Promise<ApiResponse<ConversationContextData>> {
    try {
      const response = await httpClient.get<ApiResponse<ConversationContextData>>(
        `/ai/memory/conversation/${conversationId}/context`
      );
      return response;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Clear conversation memory and session data
   */
  static async clearConversationMemory(conversationId: string): Promise<ApiResponse<null>> {
    try {
      const response = await httpClient.delete<ApiResponse<null>>(
        `/ai/memory/conversation/${conversationId}/memory`
      );
      return response;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Get memory service statistics
   */
  static async getMemoryStatistics(): Promise<ApiResponse<MemoryStatistics>> {
    try {
      const response = await httpClient.get<ApiResponse<MemoryStatistics>>(
        '/ai/memory/statistics'
      );
      return response;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Get memory service health information
   */
  static async getMemoryHealth(): Promise<ApiResponse<MemoryHealth>> {
    try {
      const response = await httpClient.get<ApiResponse<MemoryHealth>>(
        '/ai/memory/health'
      );
      return response;
    } catch (error) {
      throw error;
    }
  }
}
