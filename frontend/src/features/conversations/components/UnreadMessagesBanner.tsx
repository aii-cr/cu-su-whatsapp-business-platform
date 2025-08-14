/**
 * Unread Messages Banner component.
 * Displays a banner showing the number of unread messages, similar to WhatsApp.
 * This banner appears inline within the conversation when there are unread messages.
 */

import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/Button';
import { ChevronDownIcon } from '@heroicons/react/24/outline';

interface UnreadMessagesBannerProps {
  unreadCount: number;
  onScrollToUnread: () => void;
  className?: string;
  isVisible?: boolean; // Control visibility from parent
}

export function UnreadMessagesBanner({ 
  unreadCount, 
  onScrollToUnread, 
  className = "",
  isVisible = true
}: UnreadMessagesBannerProps) {
  const [isAnimating, setIsAnimating] = useState(false);

  // Show banner when there are unread messages and isVisible is true
  useEffect(() => {
    if (unreadCount > 0 && isVisible) {
      // Add a small delay to make the animation more noticeable
      setTimeout(() => setIsAnimating(true), 100);
    } else {
      setIsAnimating(false);
    }
  }, [unreadCount, isVisible]);

  // Don't render anything if no unread messages or not visible
  if (unreadCount === 0 || !isVisible) return null;

  const handleClick = () => {
    onScrollToUnread();
  };

  return (
    <div className={`flex justify-center my-2 ${className}`}>
      <div
        className={`
          bg-primary/10 text-primary px-3 py-1 rounded-full text-sm font-medium
          flex items-center gap-2 cursor-pointer
          transition-all duration-300 ease-in-out
          ${isAnimating 
            ? 'opacity-100 scale-100' 
            : 'opacity-0 scale-95'
          }
          hover:bg-primary/20 active:scale-95
        `}
        onClick={handleClick}
      >
        <span className="font-medium">
          {unreadCount} unread message{unreadCount !== 1 ? 's' : ''}
        </span>
        <ChevronDownIcon className="w-4 h-4" />
      </div>
    </div>
  );
}
