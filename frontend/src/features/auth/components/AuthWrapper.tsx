'use client';

/**
 * Authentication wrapper component.
 * Handles session validation and redirects on app startup.
 */

import { useEffect, useState } from 'react';
import { LoadingSpinner } from '@/components/feedback/LoadingSpinner';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';

const publicRoutes = ['/login', '/'];

export function AuthWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, user, isLoading, checkAuth, clearAuth } = useAuthStore();
  const [hasCheckedAuth, setHasCheckedAuth] = useState(false);
  const [shouldShowLoading, setShouldShowLoading] = useState(true);
  const [isRedirecting, setIsRedirecting] = useState(false);
  const isPublicRoute = publicRoutes.includes(pathname);

  useEffect(() => {
    // Check authentication status on app startup
    const performAuthCheck = async () => {
      try {
        await checkAuth();
      } catch (error) {
        console.error('Auth check failed:', error);
        // Clear auth state on error
        clearAuth();
      } finally {
        setHasCheckedAuth(true);
        // Add a small delay to prevent flash of content
        setTimeout(() => setShouldShowLoading(false), 150);
      }
    };
    
    performAuthCheck();
  }, [checkAuth, clearAuth]);

  useEffect(() => {
    // Only perform redirects after initial auth check is complete
    if (!hasCheckedAuth || isRedirecting) return;
    
    // If user is authenticated and on public route, redirect to dashboard
    if (isAuthenticated && user && isPublicRoute) {
      setIsRedirecting(true);
      router.replace('/conversations');
      return;
    }
    
    // If user is not authenticated and on protected route, redirect to login
    if (!isAuthenticated && !isPublicRoute && !isLoading) {
      setIsRedirecting(true);
      router.replace('/login');
      return;
    }
  }, [isAuthenticated, user, pathname, router, isLoading, hasCheckedAuth, isPublicRoute, isRedirecting]);

  // Show loading spinner during authentication check or if loading state is active
  // Never block public routes (e.g., /login) with the global loading screen.
  // This prevents flashes when logging in: the login button handles its own disabled/loading state.
  if (!isPublicRoute && (shouldShowLoading || isLoading || !hasCheckedAuth)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <LoadingSpinner size="lg" text="Loading..." />
      </div>
    );
  }

  // For protected routes, ensure user is authenticated before showing content
  if (!isPublicRoute && !isAuthenticated && hasCheckedAuth) {
    return null; // Don't render anything while redirecting
  }

  return <>{children}</>;
}