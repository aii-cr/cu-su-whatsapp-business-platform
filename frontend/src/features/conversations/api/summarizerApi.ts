/**
 * API client for conversation summarization.
 */

import { httpClient } from '@/lib/http';

export interface ConversationSummaryRequest {
  conversation_id: string;
  include_metadata?: boolean;
  summary_type?: string;
}

export interface ConversationSummaryResponse {
  conversation_id: string;
  summary: string;
  key_points: string[];
  sentiment?: string;
  sentiment_emoji?: string;
  topics: string[];
  metadata: Record<string, any>;
  generated_at: string;
  generated_by?: string;
  message_count: number;
  ai_message_count: number;
  human_agents: Array<{
    name: string;
    email: string;
  }>;
  customer?: {
    name: string;
    phone: string;
  };
  duration_minutes?: number;
}

export interface SummarizeResponse {
  success: boolean;
  summary?: ConversationSummaryResponse;
  error?: string;
  processing_time: number;
}

export interface CacheStatsResponse {
  total_entries: number;
  total_size_bytes: number;
  cache_ttl_seconds: number;
}

export class SummarizerApi {
  /**
   * Generate a summary for a conversation.
   */
  static async summarizeConversation(
    request: ConversationSummaryRequest
  ): Promise<SummarizeResponse> {
    const response = await httpClient.post<SummarizeResponse>('/ai/summarizer/summarize', request);
    return response;
  }

  /**
   * Get summary for a specific conversation.
   */
  static async getConversationSummary(
    conversationId: string,
    summaryType: string = 'general',
    includeMetadata: boolean = true
  ): Promise<SummarizeResponse> {
    const params = new URLSearchParams();
    params.append('summary_type', summaryType);
    params.append('include_metadata', includeMetadata.toString());
    
    const response = await httpClient.get<SummarizeResponse>(
      `/ai/summarizer/conversations/${conversationId}/summary?${params.toString()}`
    );
    return response;
  }

  /**
   * Get summarizer health status.
   */
  static async getHealth(): Promise<Record<string, any>> {
    const response = await httpClient.get<Record<string, any>>('/ai/summarizer/health');
    return response;
  }

  /**
   * Get cache statistics.
   */
  static async getCacheStats(): Promise<CacheStatsResponse> {
    const response = await httpClient.get<CacheStatsResponse>('/ai/summarizer/cache/stats');
    return response;
  }

  /**
   * Clear summarizer cache.
   */
  static async clearCache(conversationId?: string): Promise<{ message: string; data: any }> {
    let endpoint = '/ai/summarizer/cache/clear';
    if (conversationId) {
      const params = new URLSearchParams();
      params.append('conversation_id', conversationId);
      endpoint += `?${params.toString()}`;
    }
    
    const response = await httpClient.delete<{ message: string; data: any }>(endpoint);
    return response;
  }
}
