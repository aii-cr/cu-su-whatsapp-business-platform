/**
 * Departments API client functions.
 * Handles all department-related API calls to the FastAPI backend.
 */

import { httpClient, handleApiError } from '@/lib/http';
import {
  Department,
  DepartmentListResponse,
  CreateDepartmentRequest,
  UpdateDepartmentRequest,
} from '../models/department';

export class DepartmentsApi {
  /**
   * Get list of departments
   */
  static async getDepartments(): Promise<DepartmentListResponse> {
    try {
      const response = await httpClient.get<DepartmentListResponse>('/business/departments/');
      return response;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }

  /**
   * Get a specific department by ID
   */
  static async getDepartment(departmentId: string): Promise<Department> {
    try {
      const response = await httpClient.get<Department>(`/business/departments/${departmentId}`);
      return response;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }

  /**
   * Create a new department
   */
  static async createDepartment(data: CreateDepartmentRequest): Promise<Department> {
    try {
      const response = await httpClient.post<Department>('/business/departments/', data);
      return response;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }

  /**
   * Update an existing department
   */
  static async updateDepartment(
    departmentId: string,
    data: UpdateDepartmentRequest
  ): Promise<Department> {
    try {
      const response = await httpClient.put<Department>(`/business/departments/${departmentId}`, data);
      return response;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }

  /**
   * Delete a department
   */
  static async deleteDepartment(departmentId: string): Promise<void> {
    try {
      await httpClient.delete(`/business/departments/${departmentId}`);
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }

  /**
   * Add user to department
   */
  static async addUserToDepartment(departmentId: string, userId: string): Promise<Department> {
    try {
      const response = await httpClient.post<Department>(
        `/business/departments/${departmentId}/users/${userId}`
      );
      return response;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }

  /**
   * Remove user from department
   */
  static async removeUserFromDepartment(departmentId: string, userId: string): Promise<Department> {
    try {
      const response = await httpClient.delete<Department>(
        `/business/departments/${departmentId}/users/${userId}`
      );
      return response;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  }
}