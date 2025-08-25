'use client';

/**
 * Toast notification system using react-hot-toast.
 * Provides consistent styling for success, error, and info messages.
 * Includes deduplication to prevent duplicate notifications.
 */

import { toast as hotToast, Toaster } from 'react-hot-toast';
import { InformationCircleIcon } from '@heroicons/react/24/outline';

// Helper function to generate a unique ID for toast deduplication
const generateToastId = (message: string, type: string): string => {
  // Create a simple hash of the message content and type
  const content = `${type}:${message}`;
  let hash = 0;
  for (let i = 0; i < content.length; i++) {
    const char = content.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return `toast-${Math.abs(hash)}`;
};

// Custom toast functions with consistent styling and deduplication
export const toast = {
  success: (message: string) =>
    hotToast.success(message, {
      id: generateToastId(message, 'success'),
      duration: 4000,
      style: {
        background: 'rgb(var(--surface))',
        color: 'rgb(var(--foreground))',
        border: '1px solid rgb(var(--border))',
      },
      iconTheme: {
        primary: 'rgb(var(--success))',
        secondary: 'rgb(var(--background))',
      },
    }),

  error: (message: string) =>
    hotToast.error(message, {
      id: generateToastId(message, 'error'),
      duration: 5000,
      style: {
        background: 'rgb(var(--surface))',
        color: 'rgb(var(--foreground))',
        border: '1px solid rgb(var(--border))',
      },
      iconTheme: {
        primary: 'rgb(var(--error))',
        secondary: 'rgb(var(--background))',
      },
    }),

  info: (message: string) =>
    hotToast(message, {
      id: generateToastId(message, 'info'),
      duration: 4000,
      icon: <InformationCircleIcon className="w-5 h-5 text-primary-500" />,
      style: {
        background: 'rgb(var(--surface))',
        color: 'rgb(var(--foreground))',
        border: '1px solid rgb(var(--border))',
      },
    }),

  // Custom toast with custom icon and color
  custom: (message: string, icon: string, color: 'success' | 'error' | 'warning' | 'info' = 'info') =>
    hotToast(message, {
      id: generateToastId(message, 'custom'),
      duration: 4000,
      icon: icon,
      style: {
        background: 'rgb(var(--surface))',
        color: 'rgb(var(--foreground))',
        border: '1px solid rgb(var(--border))',
      },
      iconTheme: {
        primary: color === 'success' ? 'rgb(var(--success))' : 
                 color === 'error' ? 'rgb(var(--error))' : 
                 color === 'warning' ? 'rgb(var(--warning))' : 
                 'rgb(var(--primary))',
        secondary: 'rgb(var(--background))',
      },
    }),

  loading: (message: string) =>
    hotToast.loading(message, {
      id: generateToastId(message, 'loading'),
      style: {
        background: 'rgb(var(--surface))',
        color: 'rgb(var(--foreground))',
        border: '1px solid rgb(var(--border))',
      },
    }),

  dismiss: hotToast.dismiss,
  remove: hotToast.remove,
};

// Toast container component
export function ToastContainer() {
  return (
    <Toaster
      position="top-right"
      reverseOrder={false}
      gutter={8}
      containerClassName=""
      containerStyle={{}}
      toastOptions={{
        className: '',
        duration: 4000,
        style: {
          background: 'rgb(var(--surface))',
          color: 'rgb(var(--foreground))',
          border: '1px solid rgb(var(--border))',
          borderRadius: '8px',
          fontSize: '14px',
          maxWidth: '400px',
        },
        success: {
          iconTheme: {
            primary: 'rgb(var(--success))',
            secondary: 'rgb(var(--background))',
          },
        },
        error: {
          iconTheme: {
            primary: 'rgb(var(--error))',
            secondary: 'rgb(var(--background))',
          },
        },
      }}
    />
  );
}