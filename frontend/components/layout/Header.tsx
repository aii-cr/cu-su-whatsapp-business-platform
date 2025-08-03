'use client';

/**
 * Header component for the dashboard layout.
 * Contains user info, theme toggle, and navigation controls.
 */

import { useAuthStore, useUIStore } from '@/lib/store';
import { Button } from '@/components/ui/Button';
import { Avatar } from '@/components/ui/Avatar';
import { ThemeToggle } from '@/components/theme/ThemeToggle';
import { getUserDisplayName } from '@/lib/auth';
import { 
  Bars3Icon,
  ArrowRightOnRectangleIcon 
} from '@heroicons/react/24/outline';
import { toast } from '@/components/ui/Toast';

export function Header() {
  const { user, logout } = useAuthStore();
  const { toggleSidebar } = useUIStore();

  const handleLogout = async () => {
    try {
      await logout();
      toast.success('Successfully logged out');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
    <header className="h-16 border-b border-border bg-surface px-6 flex items-center justify-between">
      {/* Left side - Menu toggle */}
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
        
        <h1 className="text-lg font-semibold text-foreground">
          WhatsApp Business
        </h1>
      </div>

      {/* Right side - User info and controls */}
      <div className="flex items-center space-x-4">
        <ThemeToggle />
        
        {user && (
          <>
            <div className="hidden md:flex items-center space-x-3">
              <Avatar
                src={undefined} // No avatar support yet
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