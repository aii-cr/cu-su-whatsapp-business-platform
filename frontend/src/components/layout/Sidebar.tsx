'use client';

/**
 * Sidebar navigation component for the dashboard.
 * Contains navigation links and responsive behavior.
 */

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { useUIStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import {
  ChatBubbleLeftRightIcon,
  DocumentTextIcon,
  BuildingOfficeIcon,
  UsersIcon,
  ChartBarIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';

const navigation = [
  {
    name: 'Conversations',
    href: '/conversations',
    icon: ChatBubbleLeftRightIcon,
  },
  {
    name: 'Templates',
    href: '/templates',
    icon: DocumentTextIcon,
  },
  {
    name: 'Departments',
    href: '/departments',
    icon: BuildingOfficeIcon,
  },
  {
    name: 'Users',
    href: '/users',
    icon: UsersIcon,
  },
  {
    name: 'Analytics',
    href: '/analytics',
    icon: ChartBarIcon,
  },
  {
    name: 'Settings',
    href: '/settings',
    icon: Cog6ToothIcon,
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarOpen, setSidebarOpen } = useUIStore();

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        >
          <div className="absolute inset-0 bg-black opacity-50" />
        </div>
      )}

      {/* Sidebar */}
      <div
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 bg-surface border-r border-border transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex flex-col h-full">
          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {navigation.map((item) => {
              const isActive = pathname.startsWith(item.href);
              const Icon = item.icon;
              
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors w-full hover:bg-accent hover:text-accent-foreground',
                    isActive
                      ? 'bg-primary text-white hover:bg-primary/90'
                      : 'text-muted-foreground'
                  )}
                  onClick={() => setSidebarOpen(false)} // Close on mobile
                >
                  <Icon className="w-5 h-5 mr-3" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-border">
            <p className="text-xs text-muted-foreground text-center">
              WhatsApp Business Platform v1.0
            </p>
          </div>
        </div>
      </div>
    </>
  );
}