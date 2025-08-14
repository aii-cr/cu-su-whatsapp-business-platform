/**
 * DropdownMenu component - simple dropdown menu for action menus
 * Built with headless UI for accessibility
 */

import * as React from 'react';
import { cn } from '@/lib/utils';

export interface DropdownMenuProps {
  trigger: React.ReactNode;
  children: React.ReactNode;
  align?: 'left' | 'right';
  className?: string;
}

export function DropdownMenu({ 
  trigger, 
  children, 
  align = 'right', 
  className 
}: DropdownMenuProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const menuRef = React.useRef<HTMLDivElement>(null);
  const triggerRef = React.useRef<HTMLButtonElement>(null);

  // Close menu when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        menuRef.current &&
        !menuRef.current.contains(event.target as Node) &&
        !triggerRef.current?.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Close menu on escape key
  React.useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
        triggerRef.current?.focus();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen]);

  return (
    <div className={cn('relative', className)}>
      {/* Trigger */}
      <div 
        ref={triggerRef as any}
        onClick={() => setIsOpen(!isOpen)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setIsOpen(!isOpen);
          }
        }}
      >
        {trigger}
      </div>

      {/* Menu */}
      {isOpen && (
        <div
          ref={menuRef}
          className={cn(
            'absolute z-50 mt-1 min-w-[160px] bg-popover border border-border rounded-md shadow-lg',
            align === 'right' ? 'right-0' : 'left-0'
          )}
          role="menu"
          aria-orientation="vertical"
        >
          <div 
            className="py-1"
            onClick={() => setIsOpen(false)}
          >
            {children}
          </div>
        </div>
      )}
    </div>
  );
}

export interface DropdownMenuItemProps {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
}

export function DropdownMenuItem({ 
  children, 
  onClick, 
  disabled = false, 
  className 
}: DropdownMenuItemProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'w-full px-3 py-2 text-left text-sm transition-colors',
        'hover:bg-accent focus:bg-accent focus:outline-none',
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
      role="menuitem"
    >
      {children}
    </button>
  );
}

export default DropdownMenu;

