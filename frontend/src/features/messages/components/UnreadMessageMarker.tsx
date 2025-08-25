/**
 * Marker component for showing unread messages divider
 * Appears above the first unread message when agent enters conversation
 */

import React from 'react';
import { cn } from '@/lib/utils';

interface UnreadMessageMarkerProps {
  count: number;
  className?: string;
}

export function UnreadMessageMarker({ count, className }: UnreadMessageMarkerProps) {
  return (
    <div className={cn("flex items-center gap-3 py-3 px-4", className)}>
      <div className="flex-1 h-px bg-primary/30"></div>
      <div className="bg-primary text-primary-foreground px-3 py-1 rounded-full text-xs font-medium">
        {count} new message{count > 1 ? 's' : ''}
      </div>
      <div className="flex-1 h-px bg-primary/30"></div>
    </div>
  );
}
