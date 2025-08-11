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

export function Header() {
  const { user, logout } = useAuthStore();
  const { toggleSidebar } = useUIStore();

  const handleLogout = async () => {
    try {
      await logout();
      toast.success('Successfully logged out');
    } catch (error) {
      console.error('Logout error:', error);
      toast.error('Logout failed');
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