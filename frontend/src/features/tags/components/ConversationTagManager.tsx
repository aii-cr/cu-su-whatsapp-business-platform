/**
 * ConversationTagManager component - main interface for managing tags on conversations
 * Combines tag display, autocomplete, and tag management functionality
 */

import * as React from 'react';
import { Plus, Tag, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { TagSummary } from '../models/tag';
import { useConversationTagOperations } from '../hooks/useConversationTags';
import { TagAutocomplete } from './TagAutocomplete';
import { TagList } from './TagList';
import { Button } from '@/components/ui/Button';

export interface ConversationTagManagerProps {
  conversationId: string;
  readOnly?: boolean;
  maxTags?: number;
  showAddButton?: boolean;
  variant?: 'default' | 'compact' | 'minimal';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function ConversationTagManager({
  conversationId,
  readOnly = false,
  maxTags,
  showAddButton = true,
  variant = 'default',
  size = 'md',
  className,
}: ConversationTagManagerProps) {
  const [isAdding, setIsAdding] = React.useState(false);
  const [selectedTags, setSelectedTags] = React.useState<TagSummary[]>([]);

  const {
    conversationTags,
    isLoading,
    error,
    assignTags,
    unassignTag,
    getAssignedTags,
    isOperating,
  } = useConversationTagOperations(conversationId);

  // Convert conversation tags to tag summaries
  const currentTags = React.useMemo(() => {
    return getAssignedTags().map(tag => ({
      id: tag.id,
      name: tag.name,
      slug: tag.slug,
      display_name: tag.display_name,
      category: tag.category,
      color: tag.color,
      usage_count: 0, // We don't have usage count in denormalized data
    }));
  }, [getAssignedTags]);

  // Handle tag removal
  const handleTagRemove = React.useCallback(async (tag: TagSummary) => {
    try {
      await unassignTag(tag.id);
    } catch (error) {
      console.error('Failed to remove tag:', error);
    }
  }, [unassignTag]);

  // Handle tag assignment
  const handleTagsAdd = React.useCallback(async (tagsToAdd: TagSummary[]) => {
    if (tagsToAdd.length === 0) return;

    try {
      const tagIds = tagsToAdd.map(tag => tag.id);
      await assignTags(tagIds);
      setSelectedTags([]);
      setIsAdding(false);
    } catch (error) {
      console.error('Failed to assign tags:', error);
    }
  }, [assignTags]);

  // Handle canceling tag addition
  const handleCancel = React.useCallback(() => {
    setSelectedTags([]);
    setIsAdding(false);
  }, []);

  // Check if we can add more tags
  const canAddTags = !readOnly && (!maxTags || currentTags.length < maxTags);
  const remainingSlots = maxTags ? maxTags - currentTags.length : undefined;

  // Render loading state
  if (isLoading) {
    return (
      <div className={cn('flex items-center gap-2', className)}>
        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
        <span className="text-sm text-muted-foreground">Loading tags...</span>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className={cn('text-sm text-destructive', className)}>
        Failed to load tags
      </div>
    );
  }

  // Render minimal variant (just tags, no add functionality)
  if (variant === 'minimal') {
    return (
      <TagList
        tags={currentTags}
        variant="compact"
        size={size}
        className={className}
        emptyMessage="No tags"
      />
    );
  }

  return (
    <div className={cn('space-y-3', className)}>
      {/* Current tags */}
      {currentTags.length > 0 && (
        <TagList
          tags={currentTags}
          variant={variant === 'compact' ? 'compact' : 'default'}
          size={size}
          removable={!readOnly}
          onTagRemove={handleTagRemove}
          maxDisplay={variant === 'compact' ? 5 : undefined}
          loading={isOperating}
          disabled={readOnly}
        />
      )}

      {/* Add tags interface */}
      {!readOnly && (
        <>
          {!isAdding && canAddTags && showAddButton && (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size={size === 'lg' ? 'default' : 'sm'}
                onClick={() => setIsAdding(true)}
                disabled={isOperating}
                className="h-auto"
              >
                <Plus className="h-4 w-4 mr-1" />
                Add Tags
                {remainingSlots && (
                  <span className="ml-1 text-xs text-muted-foreground">
                    ({remainingSlots} remaining)
                  </span>
                )}
              </Button>
              
              {currentTags.length === 0 && (
                <span className="text-xs text-muted-foreground">
                  Add tags to categorize this conversation
                </span>
              )}
            </div>
          )}

          {isAdding && (
            <div className="space-y-3">
              <TagAutocomplete
                selectedTags={selectedTags}
                onTagsChange={setSelectedTags}
                placeholder="Search and select tags..."
                maxTags={remainingSlots}
                size={size}
              />
              
              {/* Always show action buttons when adding tags */}
              <div className="flex items-center gap-2">
                <Button
                  size={size === 'lg' ? 'default' : 'sm'}
                  onClick={() => handleTagsAdd(selectedTags)}
                  disabled={selectedTags.length === 0 || isOperating}
                  loading={isOperating}
                >
                  {selectedTags.length === 0 
                    ? 'Select Tags' 
                    : `Add ${selectedTags.length} Tag${selectedTags.length === 1 ? '' : 's'}`
                  }
                </Button>
                
                <Button
                  variant="outline"
                  size={size === 'lg' ? 'default' : 'sm'}
                  onClick={handleCancel}
                  disabled={isOperating}
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Read-only state message */}
      {readOnly && currentTags.length === 0 && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Tag className="h-4 w-4" />
          <span>No tags assigned</span>
        </div>
      )}

      {/* Max tags reached message */}
      {!readOnly && maxTags && currentTags.length >= maxTags && !isAdding && (
        <div className="text-xs text-muted-foreground">
          Maximum of {maxTags} tags reached
        </div>
      )}
    </div>
  );
}

export default ConversationTagManager;




