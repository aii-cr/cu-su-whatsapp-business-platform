/**
 * Conversations API client functions.
 * Handles all conversation-related API calls to the FastAPI backend.
 */

import { httpClient } from '@/lib/http';
import {
  Conversation,
  ConversationListResponse,
  ConversationFilters,
  CreateConversationRequest,
  UpdateConversationRequest,
  TransferConversationRequest,
} from '../models/conversation';

export class ConversationsApi {
  /**
   * Get list of conversations with filters and pagination
   */
  static async getConversations(filters: ConversationFilters = {}): Promise<ConversationListResponse> {
    try {
      const params = new URLSearchParams();
      
      // Add filters to query params
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, String(value));
        }
      });

      const response = await httpClient.get<ConversationListResponse>(
        `/conversations/?${params.toString()}`
      );
      return response;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Get a specific conversation by ID
   */
  static async getConversation(conversationId: string): Promise<Conversation> {
    try {
      const response = await httpClient.get<Conversation>(`/conversations/${conversationId}`);
      return response;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Create a new conversation
   */
  static async createConversation(data: CreateConversationRequest): Promise<Conversation> {
    try {
      const response = await httpClient.post<Conversation>('/conversations/', data);
      return response;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Update an existing conversation
   */
  static async updateConversation(
    conversationId: string,
    data: UpdateConversationRequest
  ): Promise<Conversation> {
    try {
      const response = await httpClient.put<Conversation>(`/conversations/${conversationId}`, data);
      return response;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Delete a conversation
   */
  static async deleteConversation(conversationId: string): Promise<void> {
    try {
      await httpClient.delete(`/conversations/${conversationId}`);
    } catch (error) {
      throw error;
    }
  }

  /**
   * Close a conversation
   */
  static async closeConversation(conversationId: string, reason?: string): Promise<Conversation> {
    try {
      const response = await httpClient.post<Conversation>(
        `/conversations/${conversationId}/close`,
        { reason }
      );
      return response;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Transfer a conversation to another department or agent
   */
  static async transferConversation(
    conversationId: string,
    data: TransferConversationRequest
  ): Promise<Conversation> {
    try {
      const response = await httpClient.post<Conversation>(
        `/conversations/${conversationId}/transfer`,
        data
      );
      return response;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Get conversation statistics
   */
  static async getConversationStats(): Promise<{
    total_conversations: number;
    active_conversations: number;
    pending_conversations: number;
    closed_conversations: number;
    unassigned_conversations: number;
    conversations_by_status: Record<string, number>;
    conversations_by_priority: Record<string, number>;
    conversations_by_channel: Record<string, number>;
    average_response_time_minutes: number;
    average_resolution_time_minutes: number;
    customer_satisfaction_rate: number;
  }> {
    try {
      const response = await httpClient.get<{
        total_conversations: number;
        active_conversations: number;
        pending_conversations: number;
        closed_conversations: number;
        unassigned_conversations: number;
        conversations_by_status: Record<string, number>;
        conversations_by_priority: Record<string, number>;
        conversations_by_channel: Record<string, number>;
        average_response_time_minutes: number;
        average_resolution_time_minutes: number;
        customer_satisfaction_rate: number;
      }>('/conversations/stats/overview');
      return response;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Claim an unassigned conversation
   */
  static async claimConversation(conversationId: string): Promise<Conversation> {
    try {
      const response = await httpClient.post<Conversation>(`/conversations/${conversationId}/claim`);
      return response;
    } catch (error) {
      throw error;
    }
  }
}