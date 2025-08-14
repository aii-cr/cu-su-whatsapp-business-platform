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

// Hex color type
export type TagColorType = string; // Hex color like "#FF5733"

// Default color palette for quick selection
export const DEFAULT_TAG_COLORS = [
  '#2563eb', // blue-600
  '#059669', // emerald-600  
  '#d97706', // amber-600
  '#dc2626', // red-600
  '#7c3aed', // violet-600
  '#db2777', // pink-600
  '#ea580c', // orange-600
  '#6b7280', // gray-500
  '#4f46e5', // indigo-600
  '#0d9488', // teal-600
  '#9333ea', // purple-600
  '#16a34a', // green-600
] as const;

// Base tag schema
export const TagSchema = z.object({
  id: z.string(),
  name: z.string().min(1).max(40),
  slug: z.string(),
  display_name: z.string().optional(),
  description: z.string().optional(),
  category: z.nativeEnum(TagCategory),
  color: z.string().regex(/^#[0-9A-Fa-f]{6}$/, "Must be a valid hex color"),
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
  color: z.string().regex(/^#[0-9A-Fa-f]{6}$/, "Must be a valid hex color"),
  usage_count: z.number().int().min(0),
});

export type TagSummary = z.infer<typeof TagSummarySchema>;

// Denormalized tag schema (stored in conversations)
export const TagDenormalizedSchema = z.object({
  id: z.string(),
  name: z.string(),
  slug: z.string(),
  category: z.nativeEnum(TagCategory),
  color: z.string().regex(/^#[0-9A-Fa-f]{6}$/, "Must be a valid hex color"),
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

// Tag create schema - simplified
export const TagCreateSchema = z.object({
  name: z.string().min(1).max(40),
  color: z.string().regex(/^#[0-9A-Fa-f]{6}$/, "Must be a valid hex color").default('#2563eb'),
  category: z.nativeEnum(TagCategory).default(TagCategory.GENERAL),
  display_name: z.string().max(60).optional(),
  description: z.string().max(200).optional(),
});

export type TagCreate = z.infer<typeof TagCreateSchema>;

// Tag update schema
export const TagUpdateSchema = z.object({
  name: z.string().min(1).max(40).optional(),
  display_name: z.string().max(60).optional(),
  description: z.string().max(200).optional(),
  category: z.nativeEnum(TagCategory).optional(),
  color: z.string().regex(/^#[0-9A-Fa-f]{6}$/, "Must be a valid hex color").optional(),
  parent_tag_id: z.string().optional(),
  department_ids: z.array(z.string()).optional(),
  user_ids: z.array(z.string()).optional(),
  is_auto_assignable: z.boolean().optional(),
  status: z.nativeEnum(TagStatus).optional(),
});

export type TagUpdate = z.infer<typeof TagUpdateSchema>;

// Tag suggestion request schema - simplified
export const TagSuggestRequestSchema = z.object({
  query: z.string().max(100).default(""),
  limit: z.number().int().min(1).max(50).default(10),
  exclude_ids: z.array(z.string()).default([]),
});

export type TagSuggestRequest = z.infer<typeof TagSuggestRequestSchema>;

// Tag suggestion response schema - matches backend structure
export const TagSuggestResponseSchema = z.object({
  suggestions: z.array(TagSummarySchema),
  total: z.number().int().min(0),
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

// Conversation tag assignment request schema - simplified
export const ConversationTagAssignRequestSchema = z.object({
  tag_ids: z.array(z.string()).min(1),
  auto_assigned: z.boolean().default(false),
});

export type ConversationTagAssignRequest = z.infer<typeof ConversationTagAssignRequestSchema>;

// Conversation tag unassign request schema
export const ConversationTagUnassignRequestSchema = z.object({
  tag_ids: z.array(z.string()).min(1),
});

export type ConversationTagUnassignRequest = z.infer<typeof ConversationTagUnassignRequestSchema>;

// Utility functions for tag operations
export function getTagColorClasses(color: TagColorType): { bg: string; text: string; border: string } {
  // Convert hex color to CSS custom properties for dynamic styling
  return {
    bg: `bg-[${color}]/10 dark:bg-[${color}]/20`,
    text: getContrastTextColor(color),
    border: `border-[${color}]/30`,
  };
}

export function getContrastTextColor(hexColor: string): string {
  // Calculate luminance to determine if text should be light or dark
  const hex = hexColor.replace('#', '');
  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);
  
  // Calculate relative luminance
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  
  // Return appropriate text color class
  return luminance > 0.5 
    ? 'text-gray-900 dark:text-gray-100' 
    : 'text-white dark:text-gray-100';
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

export function validateHexColor(color: string): boolean {
  return /^#[0-9A-Fa-f]{6}$/.test(color);
}

export function searchTags(tags: TagSummary[], query: string): TagSummary[] {
  if (!query.trim()) return tags;
  
  const lowerQuery = query.toLowerCase();
  return tags.filter(tag => 
    tag.name.toLowerCase().includes(lowerQuery) ||
    (tag.display_name && tag.display_name.toLowerCase().includes(lowerQuery))
  );
}

