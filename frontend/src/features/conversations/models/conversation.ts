/**
 * Conversation models and types for the frontend.
 * Based on the backend conversation schemas and API responses.
 */

import { z } from 'zod';
import { TagDenormalizedSchema } from '@/features/tags';

// Conversation status enum
export const ConversationStatus = {
  ACTIVE: 'active',
  PENDING: 'pending',
  CLOSED: 'closed',
  TRANSFERRED: 'transferred',
} as const;

export type ConversationStatusType = typeof ConversationStatus[keyof typeof ConversationStatus];

// Conversation priority enum  
export const ConversationPriority = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  URGENT: 'urgent',
} as const;

export type ConversationPriorityType = typeof ConversationPriority[keyof typeof ConversationPriority];

// Customer schema
export const CustomerSchema = z.object({
  phone: z.string(),
  name: z.string().optional(),
  email: z.string().email().optional(),
  avatar_url: z.string().url().optional(),
  metadata: z.record(z.string(), z.unknown()).optional(),
});

export type Customer = z.infer<typeof CustomerSchema>;

// Participant schema
export const ParticipantSchema = z.object({
  user_id: z.string(),
  name: z.string(),
  email: z.string().email(),
  joined_at: z.string(),
  role: z.string(),
});

export type Participant = z.infer<typeof ParticipantSchema>;

// Last message schema
export const LastMessageSchema = z.object({
  id: z.string(),
  content: z.string(),
  message_type: z.string(),
  sender_type: z.string(),
  timestamp: z.string(),
  is_read: z.boolean(),
});

export type LastMessage = z.infer<typeof LastMessageSchema>;

// Main conversation schema
export const ConversationSchema = z.object({
  _id: z.string(),
  customer: CustomerSchema.optional(),
  customer_name: z.string().nullable().optional(),
  customer_phone: z.string().optional(),
  participants: z.array(ParticipantSchema),
  status: z.nativeEnum(ConversationStatus),
  priority: z.nativeEnum(ConversationPriority),
  channel: z.string(),
  department_id: z.string().optional(),
  assigned_agent_id: z.string().optional(),
  tags: z.array(TagDenormalizedSchema).default([]),
  last_message: LastMessageSchema.optional(),
  unread_count: z.number().default(0),
  created_at: z.string(),
  updated_at: z.string(),
  closed_at: z.string().optional(),
  metadata: z.record(z.string(), z.unknown()).optional(),
});

export type Conversation = z.infer<typeof ConversationSchema>;

// Conversation list response schema (matching backend ConversationListResponse)
export const ConversationListResponseSchema = z.object({
  conversations: z.array(ConversationSchema),
  total: z.number(),
  page: z.number(),
  per_page: z.number(),
  pages: z.number(),
});

export type ConversationListResponse = z.infer<typeof ConversationListResponseSchema>;

// Conversation filters
export interface ConversationFilters {
  page?: number;
  per_page?: number;
  search?: string;
  status?: ConversationStatusType;
  priority?: ConversationPriorityType;
  channel?: string;
  department_id?: string;
  assigned_agent_id?: string;
  customer_type?: string;
  has_unread?: boolean;
  is_archived?: boolean;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// Create conversation request
export const CreateConversationSchema = z.object({
  customer_phone: z.string(),
  customer_name: z.string().optional(),
  initial_message: z.string(),
  department_id: z.string().optional(),
  priority: z.nativeEnum(ConversationPriority).default(ConversationPriority.MEDIUM),
  tags: z.array(TagDenormalizedSchema).default([]),
  metadata: z.record(z.string(), z.unknown()).optional(),
});

export type CreateConversationRequest = z.infer<typeof CreateConversationSchema>;

// Update conversation request
export const UpdateConversationSchema = z.object({
  status: z.nativeEnum(ConversationStatus).optional(),
  priority: z.nativeEnum(ConversationPriority).optional(),
  assigned_agent_id: z.string().optional(),
  department_id: z.string().optional(),
  tags: z.array(z.string()).optional(),
  metadata: z.record(z.string(), z.unknown()).optional(),
});

export type UpdateConversationRequest = z.infer<typeof UpdateConversationSchema>;

// Conversation statistics response (matching backend ConversationStatsResponse)
export const ConversationStatsSchema = z.object({
  total_conversations: z.number(),
  active_conversations: z.number(),
  pending_conversations: z.number(),
  closed_conversations: z.number(),
  unassigned_conversations: z.number(),
  conversations_by_status: z.record(z.string(), z.number()),
  conversations_by_priority: z.record(z.string(), z.number()),
  conversations_by_channel: z.record(z.string(), z.number()),
  average_response_time_minutes: z.number(),
  average_resolution_time_minutes: z.number(),
  customer_satisfaction_rate: z.number(),
});

export type ConversationStats = z.infer<typeof ConversationStatsSchema>;

// Transfer conversation request  
export const TransferConversationSchema = z.object({
  target_department_id: z.string().optional(),
  target_agent_id: z.string().optional(),
  reason: z.string(),
  notes: z.string().optional(),
});

export type TransferConversationRequest = z.infer<typeof TransferConversationSchema>;