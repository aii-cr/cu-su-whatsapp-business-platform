/**
 * Typing indicator component for showing when someone is typing.
 * Displays animated dots in WhatsApp style.
 */

import * as React from 'react';
import { Avatar } from '@/components/ui/Avatar';
import { cn } from '@/lib/utils';

export interface TypingIndicatorProps {
  userName?: string;
  userAvatar?: string;
  className?: string;
}

const TypingIndicator = React.forwardRef<HTMLDivElement, TypingIndicatorProps>(
  ({ userName = 'Someone', userAvatar, className }, ref) => {
    return (
      <div
        ref={ref}
        className={cn('flex items-center space-x-2 mb-4', className)}
      >
        <Avatar
          src={userAvatar}
          fallback={userName?.charAt(0) || 'U'}
          size="sm"
        />
        
        <div className="bg-surface border border-border rounded-lg px-4 py-2 shadow-sm">
          <div className="flex items-center space-x-1">
            <span className="text-sm text-muted-foreground">{userName} is typing</span>
            <div className="flex space-x-1 ml-2">
              <div className="w-1 h-1 bg-muted-foreground rounded-full animate-bounce" 
                   style={{ animationDelay: '0ms' }} />
              <div className="w-1 h-1 bg-muted-foreground rounded-full animate-bounce" 
                   style={{ animationDelay: '150ms' }} />
              <div className="w-1 h-1 bg-muted-foreground rounded-full animate-bounce" 
                   style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        </div>
      </div>
    );
  }
);
TypingIndicator.displayName = 'TypingIndicator';

export { TypingIndicator };