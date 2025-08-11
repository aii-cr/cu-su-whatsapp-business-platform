/**
 * Messages API client functions.
 * Handles all message-related API calls to the FastAPI backend.
 */

import { httpClient } from '@/lib/http';
import {
  Message,
  MessageListResponse,
  SendMessageRequest,
  MessageSendResponse,
  MessageFilters,
} from '../models/message';

export class MessagesApi {
  /**
   * Get messages for a conversation
   */
  static async getMessages(filters: MessageFilters): Promise<MessageListResponse> {
    try {
      const { conversation_id, limit = 50, offset = 0 } = filters;
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString(),
      });
      
      const response = await httpClient.get<MessageListResponse>(
        `/messages/conversation/${conversation_id}?${params}`
      );
      return response;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Send a text message
   */
  static async sendMessage(data: SendMessageRequest): Promise<MessageSendResponse> {
    try {
      const response = await httpClient.post<MessageSendResponse>('/messages/send', data);
      return response;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Send a media message (placeholder for future implementation)
   */
  static async sendMediaMessage(
    conversationId: string,
    mediaFile: File,
    caption?: string
  ): Promise<MessageSendResponse> {
    try {
      const formData = new FormData();
      formData.append('conversation_id', conversationId);
      formData.append('media', mediaFile);
      if (caption) {
        formData.append('caption', caption);
      }

      const response = await fetch(httpClient['baseUrl'] + '/messages/send/media', {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to send media message');
      }

      return await response.json();
    } catch (error) {
      throw error;
    }
  }

  /**
   * Get available message templates (placeholder for future implementation)
   */
  static async getTemplates(): Promise<any[]> {
    try {
      const response = await httpClient.get<any[]>('/messages/templates');
      return response;
    } catch (error) {
      throw error;
    }
  }
}