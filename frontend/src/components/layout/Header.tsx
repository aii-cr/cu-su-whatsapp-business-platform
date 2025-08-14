'use client';

/**
 * Header component for the dashboard layout.
 * Contains user info, theme toggle, and navigation controls.
 */

import { useAuthStore, useUIStore } from '@/lib/store';
import { Button } from '@/components/ui/Button';
import { Avatar } from '@/components/ui/Avatar';
import { ThemeToggle } from '@/components/theme/ThemeToggle';
import { BrandLogoCompact } from '@/components/layout/BrandLogo';
import { getUserDisplayName } from '@/lib/auth';
import { getProductName } from '@/lib/branding';
import { toast } from '@/components/feedback/Toast';
import { 
  Bars3Icon,
  ArrowRightOnRectangleIcon 
} from '@heroicons/react/24/outline';
import { useRouter } from 'next/navigation';
import { Input } from '@/components/ui/Input';

export function Header() {
  const { user, logout } = useAuthStore();
  const { toggleSidebar } = useUIStore();
  const router = useRouter();
  const onQuickSearch = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      const q = (e.target as HTMLInputElement).value.trim();
      if (q) router.push(`/conversations?search=${encodeURIComponent(q)}`);
    }
  };

  const handleLogout = async () => {
    try {
      // Set voluntary logout flag first
      if (typeof window !== 'undefined') {
        sessionStorage.setItem('voluntaryLogout', '1');
        console.log('Header logout - Set voluntaryLogout flag');
      }
      
      await logout();
      
      // Clear browser history and redirect to login
      if (typeof window !== 'undefined') {
        // Clear other cached state but keep the voluntaryLogout flag
        localStorage.removeItem('auth-storage');
        localStorage.removeItem('ui-storage');
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
        
        // Redirect to login page
        window.location.href = '/login';
      }
      
      // Don't show toast here - it will be shown on the login page
    } catch (error) {
      console.error('Logout error:', error);
      toast.error('Logout failed');
      
      // Even if logout fails, redirect to login
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
  };

  return (
    <header className="h-16 border-b border-border bg-surface px-6 flex items-center justify-between">
      {/* Left side - Menu toggle and branding */}
      <div className="flex items-center space-x-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          className="lg:hidden"
          aria-label="Toggle sidebar"
        >
          <Bars3Icon className="w-5 h-5" />
        </Button>
        
        {/* Brand logo and name */}
        <div className="flex items-center space-x-3">
          <BrandLogoCompact />
          <h1 className="text-lg font-semibold text-foreground hidden sm:block">
            {getProductName()}
          </h1>
        </div>
      </div>

      {/* Right side - User info and controls */}
      <div className="flex items-center space-x-4">
        <div className="hidden md:block w-64">
          <Input placeholder="Quick search…" onKeyDown={onQuickSearch} />
        </div>
        <ThemeToggle />
        
        {user && (
          <>
            <div className="hidden md:flex items-center space-x-3">
              <Avatar
                src={undefined}
                fallback={getUserDisplayName(user)}
                size="sm"
              />
              <div className="text-sm">
                <p className="font-medium text-foreground">
                  {getUserDisplayName(user)}
                </p>
                <p className="text-muted-foreground">
                  {user.email}
                </p>
              </div>
            </div>
            
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              aria-label="Logout"
            >
              <ArrowRightOnRectangleIcon className="w-5 h-5" />
            </Button>
          </>
        )}
      </div>
    </header>
  );
}