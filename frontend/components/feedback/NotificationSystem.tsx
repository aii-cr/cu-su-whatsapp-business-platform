'use client';

import { createContext, useContext, useCallback, useRef } from 'react';
import { toast as hotToast, Toaster } from 'react-hot-toast';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  InformationCircleIcon,
  XMarkIcon 
} from '@heroicons/react/24/outline';

interface NotificationContextType {
  showSuccess: (message: string, id?: string) => void;
  showError: (message: string, id?: string) => void;
  showInfo: (message: string, id?: string) => void;
  showWarning: (message: string, id?: string) => void;
  dismiss: (id?: string) => void;
  dismissAll: () => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
}

interface NotificationProviderProps {
  children: React.ReactNode;
}

export function NotificationProvider({ children }: NotificationProviderProps) {
  const activeNotifications = useRef<Set<string>>(new Set());

  const showNotification = useCallback((
    message: string, 
    type: 'success' | 'error' | 'info' | 'warning',
    id?: string
  ) => {
    const notificationId = id || `${type}-${Date.now()}`;
    
    // Prevent duplicate notifications
    if (activeNotifications.current.has(notificationId)) {
      return;
    }

    activeNotifications.current.add(notificationId);

    const toastOptions = {
      id: notificationId,
      duration: type === 'error' ? 6000 : 4000,
      style: {
        background: 'rgb(var(--surface))',
        color: 'rgb(var(--foreground))',
        border: '1px solid rgb(var(--border))',
        borderRadius: '8px',
        fontSize: '14px',
        maxWidth: '400px',
        padding: '12px 16px',
        boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -1px rgb(0 0 0 / 0.06)',
      },
      iconTheme: {
        primary: type === 'success' ? 'rgb(var(--success))' : 
                 type === 'error' ? 'rgb(var(--error))' :
                 type === 'warning' ? 'rgb(var(--warning))' : 'rgb(var(--primary))',
        secondary: 'rgb(var(--background))',
      },
    };

    const icon = type === 'success' ? <CheckCircleIcon className="w-5 h-5" /> :
                 type === 'error' ? <ExclamationTriangleIcon className="w-5 h-5" /> :
                 type === 'warning' ? <ExclamationTriangleIcon className="w-5 h-5" /> :
                 <InformationCircleIcon className="w-5 h-5" />;

    const toastOptionsWithDismiss = {
      ...toastOptions,
      onDismiss: () => {
        activeNotifications.current.delete(notificationId);
      },
    };

    hotToast[type === 'warning' ? 'error' : type](
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            {icon}
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-foreground">
              {message}
            </p>
          </div>
        </div>
        <button
          onClick={() => {
            hotToast.dismiss(notificationId);
            activeNotifications.current.delete(notificationId);
          }}
          className="flex-shrink-0 ml-3 text-muted-foreground hover:text-foreground transition-colors"
        >
          <XMarkIcon className="w-4 h-4" />
        </button>
      </div>,
      toastOptionsWithDismiss
    );
  }, []);

  const showSuccess = useCallback((message: string, id?: string) => {
    showNotification(message, 'success', id);
  }, [showNotification]);

  const showError = useCallback((message: string, id?: string) => {
    showNotification(message, 'error', id);
  }, [showNotification]);

  const showInfo = useCallback((message: string, id?: string) => {
    showNotification(message, 'info', id);
  }, [showNotification]);

  const showWarning = useCallback((message: string, id?: string) => {
    showNotification(message, 'warning', id);
  }, [showNotification]);

  const dismiss = useCallback((id?: string) => {
    if (id) {
      hotToast.dismiss(id);
      activeNotifications.current.delete(id);
    } else {
      hotToast.dismiss();
    }
  }, []);

  const dismissAll = useCallback(() => {
    hotToast.dismiss();
    activeNotifications.current.clear();
  }, []);

  return (
    <NotificationContext.Provider value={{
      showSuccess,
      showError,
      showInfo,
      showWarning,
      dismiss,
      dismissAll,
    }}>
      {children}
      <Toaster
        position="top-right"
        reverseOrder={false}
        gutter={8}
        containerClassName="z-50"
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
        }}
      />
    </NotificationContext.Provider>
  );
} 