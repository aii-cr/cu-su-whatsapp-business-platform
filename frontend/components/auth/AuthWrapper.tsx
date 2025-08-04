'use client';

/**
 * Authentication wrapper component.
 * Handles session validation and redirects on app startup.
 */

import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';

const publicRoutes = ['/login', '/'];

export function AuthWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, user, isLoading, checkAuth } = useAuthStore();
  const [hasCheckedAuth, setHasCheckedAuth] = useState(false);
  const [shouldShowLoading, setShouldShowLoading] = useState(true);

  useEffect(() => {
    // Check authentication status on app startup
    const performAuthCheck = async () => {
      await checkAuth();
      setHasCheckedAuth(true);
      // Add a small delay to prevent flash of content
      setTimeout(() => setShouldShowLoading(false), 150);
    };
    
    performAuthCheck();
  }, [checkAuth]);

  useEffect(() => {
    // Only perform redirects after initial auth check is complete
    if (!hasCheckedAuth) return;
    
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
  }, [isAuthenticated, user, pathname, router, isLoading, hasCheckedAuth]);

  // Show loading spinner during authentication check or if loading state is active
  if (shouldShowLoading || isLoading || !hasCheckedAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // For protected routes, ensure user is authenticated before showing content
  const isPublicRoute = publicRoutes.includes(pathname);
  if (!isPublicRoute && (!isAuthenticated || !user)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
          <p className="text-sm text-muted-foreground">Authenticating...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}