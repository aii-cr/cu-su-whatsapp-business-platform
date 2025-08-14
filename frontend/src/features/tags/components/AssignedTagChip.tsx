/**
 * AssignedTagChip component - displays an assigned tag with remove functionality
 * Used in the EditTagsModal for showing current conversation tags
 */

import * as React from 'react';
import { X, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { TagSummary, TagDenormalized, getTagDisplayName } from '../models/tag';
import { TagChip } from './TagChip';

export interface AssignedTagChipProps {
  tag: TagSummary | TagDenormalized;
  onRemove?: () => void;
  disabled?: boolean;
  loading?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function AssignedTagChip({
  tag,
  onRemove,
  disabled = false,
  loading = false,
  size = 'md',
  className,
}: AssignedTagChipProps) {
  const displayName = getTagDisplayName(tag);

  const handleRemove = React.useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (disabled || loading) return;
    onRemove?.();
  }, [disabled, loading, onRemove]);

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 rounded-lg border transition-all duration-150',
        size === 'sm' && 'text-xs px-2 py-1',
        size === 'md' && 'text-sm px-2.5 py-1.5',
        size === 'lg' && 'text-sm px-3 py-2',
        disabled && 'opacity-60',
        loading && 'animate-pulse',
        className
      )}
      style={{
        backgroundColor: `${tag.color}15`, // 15 = ~8% opacity in hex
        borderColor: `${tag.color}40`, // 40 = ~25% opacity in hex
        color: 'rgb(var(--foreground))', // Use CSS variable for proper theme support
      }}
    >
      {/* Tag name */}
      <span className="font-medium truncate max-w-[150px]" title={displayName}>
        {displayName}
      </span>

      {/* Remove button */}
      {onRemove && (
        <button
          type="button"
          onClick={handleRemove}
          disabled={disabled || loading}
          className={cn(
            'inline-flex items-center justify-center rounded-full transition-colors focus:outline-none focus:ring-1 focus:ring-offset-1',
            'hover:bg-black/10 dark:hover:bg-white/10',
            size === 'sm' && 'h-3 w-3',
            size === 'md' && 'h-4 w-4', 
            size === 'lg' && 'h-5 w-5',
            disabled && 'cursor-not-allowed',
            !disabled && 'cursor-pointer'
          )}
          aria-label={`Remove ${displayName} tag`}
          title={`Remove ${displayName} tag`}
        >
          {loading ? (
            <Loader2 
              className={cn(
                'animate-spin',
                size === 'sm' && 'h-2 w-2',
                size === 'md' && 'h-2.5 w-2.5',
                size === 'lg' && 'h-3 w-3'
              )} 
            />
          ) : (
            <X 
              className={cn(
                size === 'sm' && 'h-2 w-2',
                size === 'md' && 'h-2.5 w-2.5',
                size === 'lg' && 'h-3 w-3'
              )} 
            />
          )}
        </button>
      )}
    </div>
  );
}

export default AssignedTagChip;

