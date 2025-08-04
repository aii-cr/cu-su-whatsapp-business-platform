/**
 * Department models and types for the frontend.
 * Based on the backend department schemas and API responses.
 */

import { z } from 'zod';

// Department schema
export const DepartmentSchema = z.object({
  _id: z.string(),
  name: z.string(),
  description: z.string().optional(),
  is_active: z.boolean().default(true),
  users: z.array(z.string()).default([]),
  created_at: z.string(),
  updated_at: z.string(),
});

export type Department = z.infer<typeof DepartmentSchema>;

// Department list response schema
export const DepartmentListResponseSchema = z.object({
  departments: z.array(DepartmentSchema),
  pagination: z.object({
    current_page: z.number(),
    per_page: z.number(),
    total_pages: z.number(),
    total_items: z.number(),
    has_next: z.boolean(),
    has_prev: z.boolean(),
  }),
});

export type DepartmentListResponse = z.infer<typeof DepartmentListResponseSchema>;

// Create department request
export const CreateDepartmentSchema = z.object({
  name: z.string().min(1, 'Department name is required'),
  description: z.string().optional(),
  is_active: z.boolean().default(true),
});

export type CreateDepartmentRequest = z.infer<typeof CreateDepartmentSchema>;

// Update department request
export const UpdateDepartmentSchema = z.object({
  name: z.string().min(1, 'Department name is required').optional(),
  description: z.string().optional(),
  is_active: z.boolean().optional(),
});

export type UpdateDepartmentRequest = z.infer<typeof UpdateDepartmentSchema>;