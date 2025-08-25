/**
 * Message models and types for the frontend.
 * Based on the backend message schemas and API responses.
 */

import { z } from 'zod';

// Message types
export enum MessageType {
  TEXT = 'text',
  IMAGE = 'image',
  DOCUMENT = 'document',
  AUDIO = 'audio',
  VIDEO = 'video',
  STICKER = 'sticker',
  TEMPLATE = 'template',
  SYSTEM = 'system',
}

export enum MessageStatus {
  PENDING = 'pending',
  SENT = 'sent',
  DELIVERED = 'delivered', 
  READ = 'read',
  FAILED = 'failed',
}

export enum SenderType {
  CUSTOMER = 'customer',
  AGENT = 'agent',
  AI_ASSISTANT = 'ai_assistant',
  SYSTEM = 'system',
}

// Message schema (matching backend structure)
export const MessageSchema = z.object({
  _id: z.string(),
  conversation_id: z.string(),
  whatsapp_message_id: z.string().optional(),
  type: z.string(), // Backend uses "type" instead of "message_type"
  message_type: z.string().optional(), // Frontend compatibility field
  direction: z.enum(['inbound', 'outbound']), // Backend field for direction
  sender_role: z.enum(['customer', 'agent', 'ai_assistant', 'system']), // Backend field
  sender_id: z.string().optional(),
  sender_name: z.string().optional(),
  sender_phone: z.string().optional(),
  text_content: z.string().optional(),
  media_url: z.string().optional(),
  media_metadata: z.record(z.string(), z.unknown()).optional(),
  template_data: z.record(z.string(), z.unknown()).optional(),
  interactive_content: z.record(z.string(), z.unknown()).optional(),
  location_data: z.record(z.string(), z.unknown()).optional(),
  contact_data: z.record(z.string(), z.unknown()).optional(),
  content: z.object({
    text: z.string().optional(),
    media_url: z.string().optional(),
    media_type: z.string().optional(),
    file_name: z.string().optional(),
    file_size: z.number().optional(),
    caption: z.string().optional(),
  }).optional(),
  status: z.string(), // Backend uses string status
  sent_at: z.string().optional(),
  delivered_at: z.string().optional(),
  read_at: z.string().optional(),
  failed_at: z.string().optional(),
  error_code: z.string().optional(),
  error_message: z.string().optional(),
  timestamp: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  reply_to_message_id: z.string().optional(),
  is_automated: z.boolean().optional(),
  whatsapp_data: z.record(z.string(), z.unknown()).optional(),
  isOptimistic: z.boolean().optional(), // Frontend-only field for optimistic updates
});

export type Message = z.infer<typeof MessageSchema>;

// Message list response (matching backend MessageListResponse)
export const MessageListResponseSchema = z.object({
  messages: z.array(MessageSchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
});

export type MessageListResponse = z.infer<typeof MessageListResponseSchema>;

// Send message request (matching backend MessageSend)
export const SendMessageSchema = z.object({
  conversation_id: z.string().optional(),
  customer_phone: z.string().optional(),
  text_content: z.string().min(1, 'Message cannot be empty'),
  reply_to_message_id: z.string().optional(),
});

export type SendMessageRequest = z.infer<typeof SendMessageSchema>;

// Message send response (matching backend MessageSendResponse)
export const MessageSendResponseSchema = z.object({
  message: MessageSchema,
  whatsapp_response: z.record(z.string(), z.unknown()),
});

export type MessageSendResponse = z.infer<typeof MessageSendResponseSchema>;

// Message filters for pagination
export interface MessageFilters {
  conversation_id: string;
  limit?: number;
  offset?: number;
}

// Typing indicator interface
export interface TypingIndicator {
  conversation_id: string;
  user_id: string;
  user_name: string;
  is_typing: boolean;
  timestamp: string;
}