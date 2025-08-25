/**
 * ConversationTagsBar component - displays up to 5 assigned tags as chips in conversation header
 * Provides responsive overflow handling and click-to-edit functionality
 */

import * as React from 'react';
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';
import { TagSummary, getTagDisplayName } from '../models/tag';
import { TagChip } from './TagChip';
import { Button } from '@/components/ui/Button';

export interface ConversationTagsBarProps {
  conversationId: string;
  tags: TagSummary[];
  maxDisplay?: number;
  onEdit?: () => void;
  readOnly?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function ConversationTagsBar({
  conversationId,
  tags,
  maxDisplay = 5,
  onEdit,
  readOnly = false,
  size = 'md',
  className,
}: ConversationTagsBarProps) {
  const scrollRef = React.useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = React.useState(false);
  const [canScrollRight, setCanScrollRight] = React.useState(false);
  const [showOverflow, setShowOverflow] = React.useState(false);

  // Limit displayed tags
  const displayedTags = tags.slice(0, maxDisplay);
  const overflowCount = Math.max(0, tags.length - maxDisplay);

  // Check scroll state
  const updateScrollState = React.useCallback(() => {
    const container = scrollRef.current;
    if (!container) return;

    const { scrollLeft, scrollWidth, clientWidth } = container;
    setCanScrollLeft(scrollLeft > 0);
    setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 1);
  }, []);

  // Handle scroll
  const scroll = React.useCallback((direction: 'left' | 'right') => {
    const container = scrollRef.current;
    if (!container) return;

    const scrollAmount = 120; // Approximate width of a tag chip
    const newScrollLeft = direction === 'left' 
      ? container.scrollLeft - scrollAmount
      : container.scrollLeft + scrollAmount;

    container.scrollTo({ left: newScrollLeft, behavior: 'smooth' });
  }, []);

  // Set up scroll listener
  React.useEffect(() => {
    const container = scrollRef.current;
    if (!container) return;

    updateScrollState();
    container.addEventListener('scroll', updateScrollState);
    
    // Use ResizeObserver to detect when content changes
    const resizeObserver = new ResizeObserver(updateScrollState);
    resizeObserver.observe(container);

    return () => {
      container.removeEventListener('scroll', updateScrollState);
      resizeObserver.disconnect();
    };
  }, [updateScrollState, displayedTags]);

  // Handle tag click for editing
  const handleTagClick = React.useCallback(() => {
    if (!readOnly && onEdit) {
      onEdit();
    }
  }, [readOnly, onEdit]);

  // Handle keyboard navigation
  const handleKeyDown = React.useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleTagClick();
    }
  }, [handleTagClick]);

  if (displayedTags.length === 0) {
    return (
      <div className={cn(
        'flex items-center text-sm text-muted-foreground',
        className
      )}>
        <span>No tags assigned</span>
        {!readOnly && onEdit && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onEdit}
            className="ml-2 h-6 px-2 text-xs"
          >
            Add tags
          </Button>
        )}
      </div>
    );
  }

  const sizeClasses = {
    sm: 'gap-1',
    md: 'gap-1.5',
    lg: 'gap-2',
  };

  return (
    <div className={cn(
      'flex items-center',
      sizeClasses[size],
      className
    )}>
      {/* Left scroll button - only show on mobile when needed */}
      {canScrollLeft && (
        <Button
          variant="ghost"
          size="icon"
          onClick={() => scroll('left')}
          className="flex-shrink-0 h-6 w-6 sm:hidden"
          aria-label="Scroll tags left"
        >
          <ChevronLeftIcon className="h-3 w-3" />
        </Button>
      )}

      {/* Tags container */}
      <div
        ref={scrollRef}
        className={cn(
          'flex items-center min-w-0 flex-1',
          sizeClasses[size],
          // Mobile: horizontal scroll with gradient fade
          'sm:hidden overflow-x-auto scrollbar-none',
          // Tablet+: wrap layout
          'sm:flex sm:flex-wrap sm:overflow-visible'
        )}
        style={{
          // Gradient fade effect for mobile scroll
          maskImage: canScrollRight 
            ? 'linear-gradient(to right, black calc(100% - 20px), transparent)'
            : undefined,
          WebkitMaskImage: canScrollRight 
            ? 'linear-gradient(to right, black calc(100% - 20px), transparent)'
            : undefined,
        }}
      >
        {displayedTags.map((tag, index) => (
                  <TagChip
          key={tag.id}
          tag={tag}
          size={size}
          interactive={!readOnly && !!onEdit}
          onClick={handleTagClick}
          onKeyDown={handleKeyDown}
          className={cn(
            'flex-shrink-0 transition-transform hover:scale-105',
            !readOnly && onEdit && 'cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1'
          )}
          tabIndex={!readOnly && onEdit ? 0 : -1}
          role={!readOnly && onEdit ? 'button' : undefined}
          aria-label={!readOnly && onEdit ? `Edit tags (currently: ${getTagDisplayName(tag)})` : `Tag: ${getTagDisplayName(tag)}`}
        />
        ))}

        {/* Overflow indicator */}
        {overflowCount > 0 && (
          <div
            className={cn(
              'flex-shrink-0 inline-flex items-center justify-center rounded-full bg-muted text-muted-foreground font-medium',
              size === 'sm' && 'h-5 px-1.5 text-xs',
              size === 'md' && 'h-6 px-2 text-xs',
              size === 'lg' && 'h-7 px-2.5 text-sm'
            )}
            title={`${overflowCount} more tag${overflowCount === 1 ? '' : 's'}`}
          >
            +{overflowCount}
          </div>
        )}
      </div>

      {/* Right scroll button - only show on mobile when needed */}
      {canScrollRight && (
        <Button
          variant="ghost"
          size="icon"
          onClick={() => scroll('right')}
          className="flex-shrink-0 h-6 w-6 sm:hidden"
          aria-label="Scroll tags right"
        >
          <ChevronRightIcon className="h-3 w-3" />
        </Button>
      )}
    </div>
  );
}

export default ConversationTagsBar;
