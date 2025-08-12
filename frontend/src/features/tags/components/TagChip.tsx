/**
 * TagChip component - displays a tag as a colored chip/badge
 * Supports different sizes, interactive states, and accessibility
 */

import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { TagDenormalized, TagSummary, getTagColorClasses, getTagDisplayName } from '../models/tag';

const tagChipVariants = cva(
  'inline-flex items-center gap-1.5 font-medium transition-all duration-150 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2',
  {
    variants: {
      size: {
        sm: 'text-xs px-2 py-0.5 rounded-md',
        md: 'text-sm px-2.5 py-1 rounded-lg',
        lg: 'text-sm px-3 py-1.5 rounded-lg',
      },
      variant: {
        default: 'border',
        solid: '',
        outline: 'bg-transparent border',
      },
      interactive: {
        true: 'cursor-pointer hover:scale-105 active:scale-95',
        false: '',
      },
    },
    defaultVariants: {
      size: 'md',
      variant: 'default',
      interactive: false,
    },
  }
);

export interface TagChipProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof tagChipVariants> {
  tag: TagDenormalized | TagSummary;
  removable?: boolean;
  onRemove?: () => void;
  onTagClick?: () => void;
  loading?: boolean;
  disabled?: boolean;
}

const TagChip = React.forwardRef<HTMLDivElement, TagChipProps>(
  ({ 
    className, 
    tag, 
    size, 
    variant, 
    interactive: interactiveProp,
    removable = false,
    onRemove,
    onTagClick,
    loading = false,
    disabled = false,
    ...props 
  }, ref) => {
    const colorClasses = getTagColorClasses(tag.color);
    const displayName = getTagDisplayName(tag);
    const interactive = interactiveProp || !!onTagClick || removable;

    const handleClick = React.useCallback((e: React.MouseEvent) => {
      if (disabled || loading) return;
      
      e.stopPropagation();
      onTagClick?.();
    }, [disabled, loading, onTagClick]);

    const handleRemove = React.useCallback((e: React.MouseEvent) => {
      if (disabled || loading) return;
      
      e.stopPropagation();
      onRemove?.();
    }, [disabled, loading, onRemove]);

    const baseClasses = cn(
      tagChipVariants({ size, variant, interactive }),
      colorClasses.bg,
      colorClasses.text,
      variant === 'outline' || variant === 'default' ? colorClasses.border : '',
      disabled && 'opacity-60 cursor-not-allowed',
      loading && 'animate-pulse',
      className
    );

    return (
      <div
        ref={ref}
        className={baseClasses}
        onClick={onTagClick ? handleClick : undefined}
        role={onTagClick ? 'button' : undefined}
        tabIndex={onTagClick && !disabled ? 0 : undefined}
        onKeyDown={(e) => {
          if (onTagClick && !disabled && (e.key === 'Enter' || e.key === ' ')) {
            e.preventDefault();
            handleClick(e as any);
          }
        }}
        aria-label={`Tag: ${displayName}`}
        aria-disabled={disabled}
        {...props}
      >
        <span className="truncate">
          {displayName}
        </span>
        
        {removable && (
          <button
            type="button"
            className={cn(
              'ml-0.5 inline-flex items-center justify-center rounded-full hover:bg-black/10 dark:hover:bg-white/10 transition-colors focus:outline-none focus:ring-1 focus:ring-offset-1',
              size === 'sm' ? 'h-3 w-3' : size === 'lg' ? 'h-5 w-5' : 'h-4 w-4'
            )}
            onClick={handleRemove}
            disabled={disabled || loading}
            aria-label={`Remove ${displayName} tag`}
          >
            <X 
              className={cn(
                size === 'sm' ? 'h-2 w-2' : size === 'lg' ? 'h-3 w-3' : 'h-2.5 w-2.5'
              )} 
            />
          </button>
        )}
      </div>
    );
  }
);

TagChip.displayName = 'TagChip';

export { TagChip, tagChipVariants };



