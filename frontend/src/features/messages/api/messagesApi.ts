/**
 * Messages API client functions.
 * Handles message operations with the FastAPI backend.
 */

import { httpClient, handleApiError, ApiError } from '@/lib/http';
import { Message, SendMessageRequest, MessageListResponse } from '../models/message';

export interface MarkMessagesReadRequest {
  conversation_id: string;
}

export interface MarkMessagesReadResponse {
  conversation_id: string;
  messages_marked_read: number;
  timestamp: string;
}

export class MessagesApi {
  /**
   * Get messages for a conversation with pagination
   */
  static async getMessages(
    conversationId: string, 
    offset: number = 0, 
    limit: number = 50
  ): Promise<MessageListResponse> {
    try {
      const params = new URLSearchParams();
      params.append('offset', offset.toString());
      params.append('limit', limit.toString());
      
      const response = await httpClient.get<MessageListResponse>(
        `/messages/conversation/${conversationId}?${params.toString()}`
      );
      return response;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }

  /**
   * Get messages for a conversation with cursor-based pagination
   */
  static async getMessagesCursor(
    conversationId: string,
    limit: number = 50,
    before?: string
  ): Promise<{
    messages: Message[];
    next_cursor: string | null;
    has_more: boolean;
    anchor: string;
    cache_hit: boolean;
  }> {
    try {
      const params = new URLSearchParams();
      params.append('chatId', conversationId);
      params.append('limit', limit.toString());
      if (before) {
        params.append('before', before);
      }
      
      const response = await httpClient.get<{
        messages: Message[];
        next_cursor: string | null;
        has_more: boolean;
        anchor: string;
        cache_hit: boolean;
      }>(`/messages/cursor?${params.toString()}`);
      
      return response;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }

  /**
   * Get messages around a specific message ID
   */
  static async getMessagesAround(
    conversationId: string,
    anchorId: string,
    limit: number = 25
  ): Promise<{
    messages: Message[];
    next_cursor: string | null;
    has_more: boolean;
    anchor: string;
    cache_hit: boolean;
  }> {
    try {
      const params = new URLSearchParams();
      params.append('chatId', conversationId);
      params.append('anchorId', anchorId);
      params.append('limit', limit.toString());
      
      const response = await httpClient.get<{
        messages: Message[];
        next_cursor: string | null;
        has_more: boolean;
        anchor: string;
        cache_hit: boolean;
      }>(`/messages/cursor/around?${params.toString()}`);
      return response;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }

  /**
   * Send a text message
   */
  static async sendMessage(messageData: SendMessageRequest): Promise<{
    message: Message;
    whatsapp_response: any;
  }> {
    try {
      const response = await httpClient.post<{
        message: Message;
        whatsapp_response: any;
      }>(
        '/messages/send',
        messageData
      );
      return response;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }

  /**
   * Send a template message
   */
  static async sendTemplate(
    conversationId: string,
    templateName: string,
    languageCode: string = 'en_US',
    parameters: Record<string, any>[] = []
  ): Promise<Message> {
    try {
      const response = await httpClient.post<Message>(
        '/whatsapp/chat/messages/template',
        {
          conversation_id: conversationId,
          template_name: templateName,
          language_code: languageCode,
          parameters
        }
      );
      return response;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }

  /**
   * Send a media message
   */
  static async sendMedia(
    conversationId: string,
    mediaUrl: string,
    caption?: string,
    messageType: 'image' | 'audio' | 'video' | 'document' = 'image'
  ): Promise<Message> {
    try {
      const response = await httpClient.post<Message>(
        '/whatsapp/chat/messages/media',
        {
          conversation_id: conversationId,
          media_url: mediaUrl,
          caption,
          message_type: messageType
        }
      );
      return response;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }

  /**
   * Mark inbound messages as read when agent views them
   */
  static async markMessagesRead(conversationId: string): Promise<MarkMessagesReadResponse> {
    try {
      const response = await httpClient.post<MarkMessagesReadResponse>(
        '/whatsapp/chat/messages/mark-read',
        {
          conversation_id: conversationId
        }
      );
      return response;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }

  /**
   * Get available message templates
   */
  static async getTemplates(): Promise<any[]> {
    try {
      const response = await httpClient.get<any[]>('/whatsapp/chat/messages/templates');
      return response;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }

  /**
   * Send bulk messages
   */
  static async sendBulkMessages(
    conversationIds: string[],
    messageData: Omit<SendMessageRequest, 'conversation_id'>
  ): Promise<Message[]> {
    try {
      const response = await httpClient.post<Message[]>(
        '/whatsapp/chat/messages/bulk',
        {
          conversation_ids: conversationIds,
          ...messageData
        }
      );
      return response;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }
}