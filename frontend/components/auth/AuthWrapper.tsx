'use client';

/**
 * Authentication wrapper component.
 * Handles session validation and redirects on app startup.
 */

import { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';

const publicRoutes = ['/login', '/'];

export function AuthWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, user, isLoading, checkAuth } = useAuthStore();

  useEffect(() => {
    // Check authentication status on app startup
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    const isPublicRoute = publicRoutes.includes(pathname);
    
    // If user is authenticated and on public route, redirect to dashboard
    if (isAuthenticated && user && isPublicRoute) {
      router.replace('/conversations');
      return;
    }
    
    // If user is not authenticated and on protected route, redirect to login
    if (!isAuthenticated && !isPublicRoute && !isLoading) {
      router.replace('/login');
      return;
    }
  }, [isAuthenticated, user, pathname, router, isLoading]);

  // Show loading spinner during authentication check
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}