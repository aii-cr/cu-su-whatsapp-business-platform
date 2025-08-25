/**
 * Avatar component for displaying user profile pictures or initials.
 * Supports fallback to initials when image is not available.
 */

import * as React from 'react';
import { cn } from '@/lib/utils';
import { getInitials } from '@/lib/utils';

export interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  src?: string;
  alt?: string;
  fallback?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

// Helper function to check if a string is an emoji
const isEmoji = (str: string): boolean => {
  // Check if the string contains emoji characters (Unicode ranges for emojis)
  const emojiRegex = /[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F900}-\u{1F9FF}]|[\u{1F018}-\u{1F270}]|[\u{238C}-\u{2454}]|[\u{20D0}-\u{20FF}]|[\u{FE00}-\u{FE0F}]|[\u{1F000}-\u{1F02F}]|[\u{1F0A0}-\u{1F0FF}]|[\u{1F100}-\u{1F64F}]|[\u{1F910}-\u{1F96B}]|[\u{1F980}-\u{1F9E0}]/u;
  return emojiRegex.test(str);
};

const Avatar = React.forwardRef<HTMLDivElement, AvatarProps>(
  ({ className, src, alt, fallback, size = 'md', ...props }, ref) => {
    const [imageError, setImageError] = React.useState(false);
    
    const sizeClasses = {
      sm: 'h-8 w-8 text-xs',
      md: 'h-10 w-10 text-sm',
      lg: 'h-12 w-12 text-base',
      xl: 'h-16 w-16 text-lg',
    };

    const displayFallback = !src || imageError;
    
    // Handle emojis specially - display them directly without processing
    const fallbackContent = fallback ? 
      (isEmoji(fallback) ? fallback : getInitials(fallback)) : 
      '?';

    return (
      <div
        ref={ref}
        className={cn(
          'relative flex items-center justify-center rounded-full bg-muted text-muted-foreground overflow-hidden',
          sizeClasses[size],
          className
        )}
        {...props}
      >
        {!displayFallback ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={src}
            alt={alt}
            className="h-full w-full object-cover"
            onError={() => setImageError(true)}
          />
        ) : (
          <span className="font-medium">{fallbackContent}</span>
        )}
      </div>
    );
  }
);
Avatar.displayName = 'Avatar';

export { Avatar };