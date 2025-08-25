/**
 * AI Context Provider
 * Provides centralized state management for AI context sidebar across the application
 */

'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface AIContextState {
  isSidebarOpen: boolean;
  isModalOpen: boolean;
  isMobile: boolean;
}

interface AIContextActions {
  openSidebar: () => void;
  closeSidebar: () => void;
  openModal: () => void;
  closeModal: () => void;
  toggleSidebar: () => void;
}

interface AIContextValue extends AIContextState, AIContextActions {}

const AIContext = createContext<AIContextValue | undefined>(undefined);

interface AIContextProviderProps {
  children: ReactNode;
}

export const AIContextProvider: React.FC<AIContextProviderProps> = ({ children }) => {
  const [state, setState] = useState<AIContextState>({
    isSidebarOpen: false,
    isModalOpen: false,
    isMobile: false,
  });

  // Handle responsive behavior
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 1024; // lg breakpoint
      setState(prev => {
        const newState = { ...prev, isMobile: mobile };
        
        // Close sidebar on mobile
        if (mobile && prev.isSidebarOpen) {
          newState.isSidebarOpen = false;
        }
        
        return newState;
      });
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const openSidebar = () => {
    setState(prev => ({
      ...prev,
      isSidebarOpen: !prev.isMobile,
      isModalOpen: prev.isMobile,
    }));
  };

  const closeSidebar = () => {
    setState(prev => ({
      ...prev,
      isSidebarOpen: false,
    }));
  };

  const openModal = () => {
    setState(prev => ({
      ...prev,
      isModalOpen: true,
    }));
  };

  const closeModal = () => {
    setState(prev => ({
      ...prev,
      isModalOpen: false,
    }));
  };

  const toggleSidebar = () => {
    setState(prev => {
      if (prev.isMobile) {
        return {
          ...prev,
          isModalOpen: !prev.isModalOpen,
        };
      } else {
        return {
          ...prev,
          isSidebarOpen: !prev.isSidebarOpen,
        };
      }
    });
  };

  const value: AIContextValue = {
    ...state,
    openSidebar,
    closeSidebar,
    openModal,
    closeModal,
    toggleSidebar,
  };

  return (
    <AIContext.Provider value={value}>
      {children}
    </AIContext.Provider>
  );
};

export const useAIContext = (): AIContextValue => {
  const context = useContext(AIContext);
  if (!context) {
    throw new Error('useAIContext must be used within an AIContextProvider');
  }
  return context;
};
