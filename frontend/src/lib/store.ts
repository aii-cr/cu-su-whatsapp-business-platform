/**
 * Global state management using Zustand.
 * Handles authentication state and other UI state.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '@/lib/auth';
import { AuthApi } from '@/features/auth/api/authApi';

// Authentication state interface
interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  
  // Actions
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: User | null) => void;
  clearAuth: () => void;
  checkAuth: () => Promise<void>;
}

// UI state interface
interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark' | 'system';
  
  // Actions
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
}

// Authentication store
export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isLoading: false,
      isAuthenticated: false,

      login: async (email: string, password: string) => {
        set({ isLoading: true });
        try {
          // Perform login request (sets session cookie on success)
          const userFromLogin = await AuthApi.login({ email, password });

          // Some backend implementations include the user payload in the login
          // response.  If we didn't get it for some reason, fall back to an
          // explicit /me request.
          const user = userFromLogin? userFromLogin : await AuthApi.getCurrentUser();

          set({
            user,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
          });
          throw error;
        }
      },

      logout: async () => {
        set({ isLoading: true });
        try {
          await AuthApi.logout();
        } catch (error) {
          console.error('Logout error:', error);
        } finally {
          // Always clear local state regardless of API call success
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
          });
          
          // Clear all cached state to prevent back button issues
          try {
            if (typeof window !== 'undefined') {
              // Clear session storage
              sessionStorage.clear();
              sessionStorage.setItem('sessionExpired', '1');
              
              // Clear local storage
              localStorage.removeItem('auth-storage');
              localStorage.removeItem('ui-storage');
              
              // Clear any other auth-related storage
              localStorage.removeItem('user');
              localStorage.removeItem('token');
              localStorage.removeItem('session');
              
              // Force clear Zustand persisted state
              const keys = Object.keys(localStorage);
              keys.forEach(key => {
                if (key.includes('auth') || key.includes('user') || key.includes('session')) {
                  localStorage.removeItem(key);
                }
              });
            }
          } catch (storageError) {
            console.error('Error clearing storage:', storageError);
          }
        }
      },

      setUser: (user: User | null) => {
        set({
          user,
          isAuthenticated: !!user,
        });
      },

      clearAuth: () => {
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
        });
        
        // Clear any session expired flags
        try {
          if (typeof window !== 'undefined') {
            sessionStorage.removeItem('sessionExpired');
          }
        } catch {}
      },

      checkAuth: async () => {
        const state = get();
        
        // Check if session was marked as expired
        try {
          if (typeof window !== 'undefined' && sessionStorage.getItem('sessionExpired') === '1') {
            set({
              user: null,
              isAuthenticated: false,
              isLoading: false,
            });
            return;
          }
        } catch {}
        
        // Always validate session with backend, even if we have cached state
        // This prevents back button issues where cached state exists but session is invalid
        set({ isLoading: true });
        try {
          const user = await AuthApi.getCurrentUser();
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          // Session is invalid, clear all cached state
          console.log('Auth check failed - user not authenticated');
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
          });
          
          // Clear cached state since session is invalid
          try {
            if (typeof window !== 'undefined') {
              sessionStorage.setItem('sessionExpired', '1');
              localStorage.removeItem('auth-storage');
              localStorage.removeItem('ui-storage');
            }
          } catch (storageError) {
            console.error('Error clearing storage on auth failure:', storageError);
          }
        }
      }
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        user: state.user,
      }),
    }
  )
);

// UI state store
export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: 'system',

      setSidebarOpen: (open: boolean) => set({ sidebarOpen: open }),
      
      toggleSidebar: () =>
        set((state) => ({ sidebarOpen: !state.sidebarOpen })),

      setTheme: (theme: 'light' | 'dark' | 'system') => set({ theme }),
    }),
    {
      name: 'ui-storage',
    }
  )
);