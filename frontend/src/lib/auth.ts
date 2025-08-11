/**
 * Authentication utilities and types for the WhatsApp Business platform.
 * Handles user session management and permission checks.
 */

import { z } from 'zod';

// User schema based on backend User model
export const UserSchema = z.object({
  _id: z.string(),
  first_name: z.string(),
  last_name: z.string(),
  email: z.string().email(),
  phone: z.string().optional(),
  role_ids: z.array(z.string()),
  department_id: z.string().optional(),
  permissions: z.array(z.string()),
  is_active: z.boolean(),
  is_verified: z.boolean(),
  created_at: z.string(),
  updated_at: z.string(),
  last_login: z.string().optional(),
});

export type User = z.infer<typeof UserSchema>;

// Login schema
export const LoginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
});

export type LoginCredentials = z.infer<typeof LoginSchema>;

// User registration schema
export const RegisterSchema = z.object({
  first_name: z.string().min(1, 'First name is required'),
  last_name: z.string().min(1, 'Last name is required'),
  email: z.string().email('Please enter a valid email address'),
  phone: z.string().optional(),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  role_ids: z.array(z.string()),
  department_id: z.string().optional(),
});

export type RegisterData = z.infer<typeof RegisterSchema>;

// Authentication response from backend
export const AuthResponseSchema = z.object({
  message: z.string(),
  data: UserSchema,
});

export type AuthResponse = z.infer<typeof AuthResponseSchema>;

/**
 * Check if user has a specific permission
 */
export function hasPermission(user: User | null, permission: string): boolean {
  if (!user || !user.is_active) return false;
  return user.permissions.includes(permission) || user.permissions.includes('*');
}

/**
 * Check if user has any of the specified permissions
 */
export function hasAnyPermission(user: User | null, permissions: string[]): boolean {
  if (!user || !user.is_active) return false;
  return permissions.some(permission => hasPermission(user, permission));
}

/**
 * Check if user has all of the specified permissions
 */
export function hasAllPermissions(user: User | null, permissions: string[]): boolean {
  if (!user || !user.is_active) return false;
  return permissions.every(permission => hasPermission(user, permission));
}

/**
 * Get user display name
 */
export function getUserDisplayName(user: User): string {
  return `${user.first_name} ${user.last_name}`;
}

/**
 * Check if user is super admin (has all permissions)
 */
export function isSuperAdmin(user: User | null): boolean {
  return hasPermission(user, '*');
}