/**
 * Banner component for showing unread messages count in message list
 * Appears when user scrolls up and receives new messages
 */

import React from 'react';
import { ChevronDownIcon } from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';

interface NewMessagesBannerProps {
  count: number;
  onClick: () => void;
  className?: string;
}

export function NewMessagesBanner({ count, onClick, className }: NewMessagesBannerProps) {
  return (
    <div 
      className={cn(
        "fixed bottom-20 left-1/2 transform -translate-x-1/2 z-50",
        "bg-primary text-primary-foreground px-4 py-2 rounded-full shadow-lg",
        "flex items-center gap-2 cursor-pointer transition-all duration-300",
        "hover:bg-primary/90 animate-in slide-in-from-bottom-2 fade-in",
        className
      )}
      onClick={onClick}
    >
      <span className="text-sm font-medium">
        {count} new message{count > 1 ? 's' : ''}
      </span>
      <ChevronDownIcon className="h-4 w-4" />
    </div>
  );
}
