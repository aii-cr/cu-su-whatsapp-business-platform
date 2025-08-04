'use client';

/**
 * Toast notification system using react-hot-toast.
 * Provides consistent styling for success, error, and info messages.
 */

import { toast as hotToast, Toaster } from 'react-hot-toast';
import { InformationCircleIcon } from '@heroicons/react/24/outline';

// Custom toast functions with consistent styling
export const toast = {
  success: (message: string) =>
    hotToast.success(message, {
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
      duration: 4000,
      icon: <InformationCircleIcon className="w-5 h-5 text-primary-500" />,
      style: {
        background: 'rgb(var(--surface))',
        color: 'rgb(var(--foreground))',
        border: '1px solid rgb(var(--border))',
      },
    }),

  loading: (message: string) =>
    hotToast.loading(message, {
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