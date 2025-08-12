/**
 * Tag models and types for the frontend.
 * Based on the backend tag schemas and API responses.
 */

import { z } from 'zod';

// Tag status enum
export const TagStatus = {
  ACTIVE: 'active',
  INACTIVE: 'inactive',
} as const;

export type TagStatusType = typeof TagStatus[keyof typeof TagStatus];

// Tag category enum
export const TagCategory = {
  GENERAL: 'general',
  DEPARTMENT: 'department',
  PRIORITY: 'priority',
  CUSTOMER_TYPE: 'customer_type',
  ISSUE_TYPE: 'issue_type',
  PRODUCT: 'product',
  STATUS: 'status',
  CUSTOM: 'custom',
} as const;

export type TagCategoryType = typeof TagCategory[keyof typeof TagCategory];

// Tag color enum
export const TagColor = {
  BLUE: 'blue',
  GREEN: 'green',
  YELLOW: 'yellow',
  RED: 'red',
  PURPLE: 'purple',
  PINK: 'pink',
  ORANGE: 'orange',
  GRAY: 'gray',
  INDIGO: 'indigo',
  TEAL: 'teal',
} as const;

export type TagColorType = typeof TagColor[keyof typeof TagColor];

// Color palette mapping for UI
export const TagColorPalette: Record<TagColorType, { bg: string; text: string; border: string }> = {
  [TagColor.BLUE]: {
    bg: 'bg-blue-100 dark:bg-blue-900/20',
    text: 'text-blue-800 dark:text-blue-200',
    border: 'border-blue-200 dark:border-blue-700',
  },
  [TagColor.GREEN]: {
    bg: 'bg-emerald-100 dark:bg-emerald-900/20',
    text: 'text-emerald-800 dark:text-emerald-200',
    border: 'border-emerald-200 dark:border-emerald-700',
  },
  [TagColor.YELLOW]: {
    bg: 'bg-amber-100 dark:bg-amber-900/20',
    text: 'text-amber-800 dark:text-amber-200',
    border: 'border-amber-200 dark:border-amber-700',
  },
  [TagColor.RED]: {
    bg: 'bg-red-100 dark:bg-red-900/20',
    text: 'text-red-800 dark:text-red-200',
    border: 'border-red-200 dark:border-red-700',
  },
  [TagColor.PURPLE]: {
    bg: 'bg-purple-100 dark:bg-purple-900/20',
    text: 'text-purple-800 dark:text-purple-200',
    border: 'border-purple-200 dark:border-purple-700',
  },
  [TagColor.PINK]: {
    bg: 'bg-pink-100 dark:bg-pink-900/20',
    text: 'text-pink-800 dark:text-pink-200',
    border: 'border-pink-200 dark:border-pink-700',
  },
  [TagColor.ORANGE]: {
    bg: 'bg-orange-100 dark:bg-orange-900/20',
    text: 'text-orange-800 dark:text-orange-200',
    border: 'border-orange-200 dark:border-orange-700',
  },
  [TagColor.GRAY]: {
    bg: 'bg-gray-100 dark:bg-gray-900/20',
    text: 'text-gray-800 dark:text-gray-200',
    border: 'border-gray-200 dark:border-gray-700',
  },
  [TagColor.INDIGO]: {
    bg: 'bg-indigo-100 dark:bg-indigo-900/20',
    text: 'text-indigo-800 dark:text-indigo-200',
    border: 'border-indigo-200 dark:border-indigo-700',
  },
  [TagColor.TEAL]: {
    bg: 'bg-teal-100 dark:bg-teal-900/20',
    text: 'text-teal-800 dark:text-teal-200',
    border: 'border-teal-200 dark:border-teal-700',
  },
};

// Base tag schema
export const TagSchema = z.object({
  id: z.string(),
  name: z.string().min(1).max(40),
  slug: z.string(),
  display_name: z.string().optional(),
  description: z.string().optional(),
  category: z.nativeEnum(TagCategory),
  color: z.nativeEnum(TagColor),
  parent_tag_id: z.string().optional(),
  child_tags: z.array(z.string()).default([]),
  status: z.nativeEnum(TagStatus),
  is_system_tag: z.boolean(),
  is_auto_assignable: z.boolean(),
  usage_count: z.number().int().min(0),
  department_ids: z.array(z.string()).default([]),
  user_ids: z.array(z.string()).default([]),
  created_at: z.string(),
  updated_at: z.string(),
  created_by: z.string().optional(),
  updated_by: z.string().optional(),
});

export type Tag = z.infer<typeof TagSchema>;

// Tag summary schema (for autocomplete and lightweight lists)
export const TagSummarySchema = z.object({
  id: z.string(),
  name: z.string(),
  slug: z.string(),
  display_name: z.string().optional(),
  category: z.nativeEnum(TagCategory),
  color: z.nativeEnum(TagColor),
  usage_count: z.number().int().min(0),
});

export type TagSummary = z.infer<typeof TagSummarySchema>;

// Denormalized tag schema (stored in conversations)
export const TagDenormalizedSchema = z.object({
  id: z.string(),
  name: z.string(),
  slug: z.string(),
  category: z.nativeEnum(TagCategory),
  color: z.nativeEnum(TagColor),
  display_name: z.string().optional(),
});

export type TagDenormalized = z.infer<typeof TagDenormalizedSchema>;

// Conversation tag assignment schema
export const ConversationTagSchema = z.object({
  conversation_id: z.string(),
  tag: TagDenormalizedSchema,
  assigned_at: z.string(),
  assigned_by: z.string().optional(),
  auto_assigned: z.boolean(),
  confidence_score: z.number().min(0).max(1).optional(),
});

export type ConversationTag = z.infer<typeof ConversationTagSchema>;

// Tag create schema
export const TagCreateSchema = z.object({
  name: z.string().min(1).max(40),
  display_name: z.string().max(60).optional(),
  description: z.string().max(200).optional(),
  category: z.nativeEnum(TagCategory).default(TagCategory.GENERAL),
  color: z.nativeEnum(TagColor).default(TagColor.BLUE),
  parent_tag_id: z.string().optional(),
  department_ids: z.array(z.string()).default([]),
  user_ids: z.array(z.string()).default([]),
  is_auto_assignable: z.boolean().default(true),
});

export type TagCreate = z.infer<typeof TagCreateSchema>;

// Tag update schema
export const TagUpdateSchema = z.object({
  name: z.string().min(1).max(40).optional(),
  display_name: z.string().max(60).optional(),
  description: z.string().max(200).optional(),
  category: z.nativeEnum(TagCategory).optional(),
  color: z.nativeEnum(TagColor).optional(),
  parent_tag_id: z.string().optional(),
  department_ids: z.array(z.string()).optional(),
  user_ids: z.array(z.string()).optional(),
  is_auto_assignable: z.boolean().optional(),
  status: z.nativeEnum(TagStatus).optional(),
});

export type TagUpdate = z.infer<typeof TagUpdateSchema>;

// Tag suggestion request schema
export const TagSuggestRequestSchema = z.object({
  query: z.string().min(1).max(100),
  category: z.nativeEnum(TagCategory).optional(),
  limit: z.number().int().min(1).max(50).default(10),
  exclude_ids: z.array(z.string()).default([]),
});

export type TagSuggestRequest = z.infer<typeof TagSuggestRequestSchema>;

// Tag suggestion response schema
export const TagSuggestResponseSchema = z.object({
  tags: z.array(TagSummarySchema),
  total: z.number().int().min(0),
  query: z.string(),
});

export type TagSuggestResponse = z.infer<typeof TagSuggestResponseSchema>;

// Tag list request schemaNTEND
export const TagListRequestSchema = z.object({
  category: z.nativeEnum(TagCategory).optional(),
  status: z.nativeEnum(TagStatus).optional(),
  department_id: z.string().optional(),
  search: z.string().max(100).optional(),
  parent_tag_id: z.string().optional(),
  limit: z.number().int().min(1).max(200).default(50),
  offset: z.number().int().min(0).default(0),
  sort_by: z.enum(['name', 'category', 'usage_count', 'created_at', 'updated_at']).default('name'),
  sort_order: z.enum(['asc', 'desc']).default('asc'),
});

export type TagListRequest = z.infer<typeof TagListRequestSchema>;

// Tag list response schema
export const TagListResponseSchema = z.object({
  tags: z.array(TagSchema),
  total: z.number().int().min(0),
  limit: z.number().int().min(1),
  offset: z.number().int().min(0),
  has_more: z.boolean(),
});

export type TagListResponse = z.infer<typeof TagListResponseSchema>;

// Conversation tag assignment request schema
export const ConversationTagAssignRequestSchema = z.object({
  tag_ids: z.array(z.string()).min(1),
  auto_assigned: z.boolean().default(false),
  confidence_scores: z.record(z.string(), z.number().min(0).max(1)).optional(),
});

export type ConversationTagAssignRequest = z.infer<typeof ConversationTagAssignRequestSchema>;

// Conversation tag unassign request schema
export const ConversationTagUnassignRequestSchema = z.object({
  tag_ids: z.array(z.string()).min(1),
});

export type ConversationTagUnassignRequest = z.infer<typeof ConversationTagUnassignRequestSchema>;

// Utility functions for tag operations
export function getTagColorClasses(color: TagColorType): { bg: string; text: string; border: string } {
  return TagColorPalette[color] || TagColorPalette[TagColor.GRAY];
}

export function getTagDisplayName(tag: Tag | TagSummary | TagDenormalized): string {
  return tag.display_name || tag.name;
}

export function formatTagCategory(category: TagCategoryType): string {
  const formatted = category.replace(/_/g, ' ').toLowerCase();
  return formatted.charAt(0).toUpperCase() + formatted.slice(1);
}

export function isSystemTag(tag: Pick<Tag, 'is_system_tag'>): boolean {
  return tag.is_system_tag;
}

export function isTagActive(tag: Pick<Tag, 'status'>): boolean {
  return tag.status === TagStatus.ACTIVE;
}

export function sortTagsByUsage(tags: TagSummary[]): TagSummary[] {
  return [...tags].sort((a, b) => b.usage_count - a.usage_count);
}

export function sortTagsByName(tags: TagSummary[]): TagSummary[] {
  return [...tags].sort((a, b) => a.name.localeCompare(b.name));
}

export function filterTagsByCategory(tags: TagSummary[], category?: TagCategoryType): TagSummary[] {
  if (!category) return tags;
  return tags.filter(tag => tag.category === category);
}

export function searchTags(tags: TagSummary[], query: string): TagSummary[] {
  if (!query.trim()) return tags;
  
  const lowerQuery = query.toLowerCase();
  return tags.filter(tag => 
    tag.name.toLowerCase().includes(lowerQuery) ||
    (tag.display_name && tag.display_name.toLowerCase().includes(lowerQuery))
  );
}

