/**
 * QuickAddTags component - displays most frequently used tags for quick selection
 */

import * as React from 'react';
import { Tag, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { TagSummary } from '../models/tag';
import { TagChip } from './TagChip';
import { useQuickAddTags } from '../hooks/useQuickAddTags';

export interface QuickAddTagsProps {
  onTagSelect: (tag: TagSummary) => void;
  excludeTagIds?: string[];
  limit?: number;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showTitle?: boolean;
  disabled?: boolean;
}

export function QuickAddTags({
  onTagSelect,
  excludeTagIds = [],
  limit = 7,
  className,
  size = 'md',
  showTitle = true,
  disabled = false,
}: QuickAddTagsProps) {
  const {
    data: quickAddResponse,
    isLoading,
    error,
  } = useQuickAddTags({
    limit,
    enabled: true,
  });

  const quickAddTags = quickAddResponse?.suggestions || [];
  
  // Filter out excluded tags
  const availableTags = quickAddTags.filter(
    tag => !excludeTagIds.includes(tag.id)
  );



  const handleTagClick = React.useCallback((tag: TagSummary) => {
    if (!disabled) {
      onTagSelect(tag);
    }
  }, [onTagSelect, disabled]);

  if (isLoading) {
    return (
      <div className={cn('flex items-center justify-center py-4', className)}>
        <Loader2 className="h-4 w-4 animate-spin mr-2" />
        <span className="text-sm text-muted-foreground">Loading quick add tags...</span>
      </div>
    );
  }

  if (error) {
    console.error('Error loading quick add tags:', error);
    return null; // Don't show error state, just don't render
  }

  if (availableTags.length === 0) {
    return null; // Don't render if no tags available
  }

  const sizeClasses = {
    sm: 'gap-1.5',
    md: 'gap-2',
    lg: 'gap-2.5',
  };

  return (
    <div className={cn('space-y-3', className)}>
      {showTitle && (
        <div className="flex items-center gap-2">
          <Tag className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-sm font-medium text-foreground">
            Quick Add Tags
          </h3>
          <span className="text-xs text-muted-foreground">
            ({availableTags.length} available)
          </span>
        </div>
      )}
      
      <div className={cn(
        'flex flex-wrap',
        sizeClasses[size]
      )}>
        {availableTags.map((tag) => (
          <button
            key={tag.id}
            type="button"
            onClick={() => handleTagClick(tag)}
            disabled={disabled}
            className={cn(
              'transition-all duration-200',
              'hover:scale-105 active:scale-95',
              'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary',
              disabled && 'opacity-50 cursor-not-allowed',
              !disabled && 'cursor-pointer'
            )}
            aria-label={`Quick add tag: ${tag.display_name || tag.name}`}
          >
            <TagChip
              tag={tag}
              size={size}
              variant="outline"
              className={cn(
                'border-2',
                !disabled && 'hover:border-primary hover:bg-primary/5',
                disabled && 'pointer-events-none'
              )}
            />
          </button>
        ))}
      </div>
    </div>
  );
}

export default QuickAddTags;
