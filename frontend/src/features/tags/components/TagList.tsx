/**
 * TagList component - displays a list of tags with optional actions
 * Supports different layouts and interaction patterns
 */

import * as React from 'react';
import { cn } from '@/lib/utils';
import { TagDenormalized, TagSummary } from '../models/tag';
import { TagChip } from './TagChip';

export interface TagListProps extends React.HTMLAttributes<HTMLDivElement> {
  tags: (TagDenormalized | TagSummary)[];
  variant?: 'default' | 'compact' | 'grid';
  size?: 'sm' | 'md' | 'lg';
  removable?: boolean;
  onTagRemove?: (tag: TagDenormalized | TagSummary) => void;
  onTagClick?: (tag: TagDenormalized | TagSummary) => void;
  maxDisplay?: number;
  showMore?: boolean;
  emptyMessage?: string;
  loading?: boolean;
  disabled?: boolean;
}

export function TagList({
  tags,
  variant = 'default',
  size = 'md',
  removable = false,
  onTagRemove,
  onTagClick,
  maxDisplay,
  showMore = true,
  emptyMessage = 'No tags',
  loading = false,
  disabled = false,
  className,
  ...props
}: TagListProps) {
  const [showAll, setShowAll] = React.useState(false);
  
  // Determine which tags to display
  const displayTags = React.useMemo(() => {
    if (!maxDisplay || showAll) return tags;
    return tags.slice(0, maxDisplay);
  }, [tags, maxDisplay, showAll]);
  
  const hasMore = maxDisplay && tags.length > maxDisplay && !showAll;
  const hiddenCount = hasMore ? tags.length - maxDisplay : 0;

  // Handle tag removal
  const handleTagRemove = React.useCallback((tag: TagDenormalized | TagSummary) => {
    if (disabled || loading) return;
    onTagRemove?.(tag);
  }, [disabled, loading, onTagRemove]);

  // Handle tag click
  const handleTagClick = React.useCallback((tag: TagDenormalized | TagSummary) => {
    if (disabled || loading) return;
    onTagClick?.(tag);
  }, [disabled, loading, onTagClick]);

  // Render empty state
  if (tags.length === 0 && !loading) {
    return (
      <div className={cn('text-sm text-muted-foreground', className)} {...props}>
        {emptyMessage}
      </div>
    );
  }

  // Render loading state
  if (loading) {
    return (
      <div className={cn('flex flex-wrap gap-2', className)} {...props}>
        {Array.from({ length: 3 }).map((_, index) => (
          <div
            key={index}
            className={cn(
              'animate-pulse rounded-lg bg-muted',
              size === 'sm' ? 'h-6 w-16' : size === 'lg' ? 'h-8 w-20' : 'h-7 w-18'
            )}
          />
        ))}
      </div>
    );
  }

  const containerClasses = cn(
    'flex items-center',
    {
      'flex-wrap gap-2': variant === 'default' || variant === 'grid',
      'flex-wrap gap-1': variant === 'compact',
      'grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2': variant === 'grid',
    },
    className
  );

  return (
    <div className={containerClasses} {...props}>
      {/* Display tags */}
      {displayTags.map((tag) => (
        <TagChip
          key={tag.id}
          tag={tag}
          size={variant === 'compact' ? 'sm' : size}
          removable={removable}
          onRemove={removable ? () => handleTagRemove(tag) : undefined}
          onTagClick={onTagClick ? () => handleTagClick(tag) : undefined}
          disabled={disabled}
          loading={loading}
        />
      ))}
      
      {/* Show more button */}
      {hasMore && showMore && (
        <button
          type="button"
          onClick={() => setShowAll(true)}
          disabled={disabled || loading}
          className={cn(
            'inline-flex items-center justify-center rounded-lg border border-dashed border-border bg-transparent transition-colors hover:bg-accent hover:text-accent-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
            size === 'sm' ? 'text-xs px-2 py-0.5' : size === 'lg' ? 'text-sm px-3 py-1.5' : 'text-sm px-2.5 py-1',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
          aria-label={`Show ${hiddenCount} more tags`}
        >
          +{hiddenCount} more
        </button>
      )}
      
      {/* Show less button */}
      {maxDisplay && showAll && tags.length > maxDisplay && (
        <button
          type="button"
          onClick={() => setShowAll(false)}
          disabled={disabled || loading}
          className={cn(
            'inline-flex items-center justify-center rounded-lg border border-dashed border-border bg-transparent transition-colors hover:bg-accent hover:text-accent-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
            size === 'sm' ? 'text-xs px-2 py-0.5' : size === 'lg' ? 'text-sm px-3 py-1.5' : 'text-sm px-2.5 py-1',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
          aria-label="Show fewer tags"
        >
          Show less
        </button>
      )}
    </div>
  );
}

export default TagList;





