/**
 * EditTagsModal component - modal interface for editing conversation tags
 * Includes tag search, create-on-the-fly, color picker, and assigned tag management
 */

import * as React from 'react';
import { X, Plus, Loader2, AlertCircle, Tag } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/Dialog';
import { Button } from '@/components/ui/Button';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { TagSummary } from '../models/tag';
import { TagTypeahead } from './TagTypeahead';
import { AssignedTagChip } from './AssignedTagChip';
import { QuickAddTags } from './QuickAddTags';
import { TagUnassignConfirmModal } from './TagUnassignConfirmModal';
import { useConversationTagOperations } from '../hooks/useConversationTags';

export interface EditTagsModalProps {
  conversationId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  className?: string;
}

export function EditTagsModal({
  conversationId,
  open,
  onOpenChange,
  className,
}: EditTagsModalProps) {
  const [selectedTags, setSelectedTags] = React.useState<TagSummary[]>([]);
  const [isProcessing, setIsProcessing] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [unassignModal, setUnassignModal] = React.useState<{
    open: boolean;
    tag: TagSummary | null;
  }>({ open: false, tag: null });

  const {
    conversationTags,
    isLoading,
    error: isError,
    assignTags,
    unassignTag,
    isAssigning,
    isUnassigning,
    tagSettings,
  } = useConversationTagOperations(conversationId);

  // Reset state when modal opens/closes
  React.useEffect(() => {
    if (open) {
      setSelectedTags([]);
      setError(null);
      setUnassignModal({ open: false, tag: null });
    }
  }, [open]);

  // Check if we can add more tags using backend-provided limit
  const limit = tagSettings?.max_tags_per_conversation ?? 10;
  const currentTagCount = conversationTags?.length || 0;
  const canAddTags = currentTagCount < limit;
  const remainingSlots = Math.max(0, limit - currentTagCount);

  // Debug logging for suggestions
  React.useEffect(() => {
    console.log('🔍 [EditTagsModal] Modal state:', {
      conversationId,
      open,
      conversationTags: conversationTags?.length || 0,
      tagSettings,
      limit,
      currentTagCount,
      canAddTags,
      remainingSlots,
    });
  }, [conversationId, open, conversationTags, tagSettings, limit, currentTagCount, canAddTags, remainingSlots]);

  // Handle assigning selected tags
  const handleAssignTags = React.useCallback(async () => {
    if (selectedTags.length === 0) return;

    setIsProcessing(true);
    setError(null);

    try {
      const tagIds = selectedTags.map(tag => tag.id);
      await assignTags(tagIds);
      setSelectedTags([]);
      
      // Announce success to screen readers
      const tagNames = selectedTags.map(t => t.display_name || t.name).join(', ');
      const announcement = selectedTags.length === 1 
        ? `Added tag ${tagNames}` 
        : `Added ${selectedTags.length} tags: ${tagNames}`;
      
      // Use a more accessible announcement method
      setTimeout(() => {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = `Successfully ${selectedTags.length === 1 ? 'added tag' : `added ${selectedTags.length} tags`}`;
        document.body.appendChild(announcement);
        setTimeout(() => document.body.removeChild(announcement), 1000);
      }, 100);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to assign tags');
    } finally {
      setIsProcessing(false);
    }
  }, [selectedTags, assignTags]);

  // Handle quick add tag selection
  const handleQuickAddTag = React.useCallback(async (tag: TagSummary) => {
    try {
      await assignTags([tag.id]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to assign quick add tag');
    }
  }, [assignTags]);

  // Handle unassigning a tag with custom confirmation
  const handleUnassignTag = React.useCallback(async (tag: TagSummary) => {
    setUnassignModal({ open: true, tag });
  }, []);

  // Handle unassign confirmation
  const handleUnassignConfirm = React.useCallback(async () => {
    if (!unassignModal.tag) return;

    setError(null);

    try {
      await unassignTag(unassignModal.tag.id);
      
      // Announce removal to screen readers
      setTimeout(() => {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = `Removed tag ${unassignModal.tag?.display_name || unassignModal.tag?.name}`;
        document.body.appendChild(announcement);
        setTimeout(() => document.body.removeChild(announcement), 1000);
      }, 100);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to unassign tag');
    }
  }, [unassignModal.tag, unassignTag]);

  // Handle unassign cancel
  const handleUnassignCancel = React.useCallback(() => {
    // Just close the modal, no action needed
  }, []);

  // Filter out already assigned tags from selection
  const assignedTagIds = new Set(conversationTags?.map((ct: any) => ct.tag.id) || []);
  const availableSelectedTags = selectedTags.filter(tag => !assignedTagIds.has(tag.id));

  // Validate selection doesn't exceed limit
  const wouldExceedLimit = currentTagCount + availableSelectedTags.length > limit;

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent 
          className={cn(
            'sm:max-w-3xl lg:max-w-4xl w-full max-h-[95vh] overflow-hidden flex flex-col relative z-[1000]',
            className
          )}
          aria-describedby="edit-tags-description"
        >
          <DialogHeader className="flex-shrink-0">
            <DialogTitle>Edit Conversation Tags</DialogTitle>
            <p id="edit-tags-description" className="text-sm text-muted-foreground">
              Add or remove tags to categorize this conversation. Maximum {limit} tags allowed.
            </p>
          </DialogHeader>

          <div className="flex-1 overflow-y-auto flex flex-col space-y-6 p-6">
            {/* Error display */}
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Current tags section */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium">
                  Current Tags ({currentTagCount}/{limit})
                </h3>
                {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
              </div>

              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  <span className="ml-2 text-sm text-muted-foreground">Loading tags...</span>
                </div>
              ) : isError ? (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>Failed to load conversation tags</AlertDescription>
                </Alert>
              ) : conversationTags && conversationTags.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {conversationTags.map((convTag: any) => (
                    <AssignedTagChip
                      key={convTag.tag.id}
                      tag={convTag.tag}
                      onRemove={() => handleUnassignTag(convTag.tag)}
                      disabled={isUnassigning}
                      size="md"
                    />
                  ))}
                </div>
              ) : (
                <div className="text-sm text-muted-foreground py-6 text-center border-2 border-dashed border-muted rounded-lg">
                  <Tag className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No tags assigned yet</p>
                  <p className="text-xs mt-1">Add tags to categorize this conversation</p>
                </div>
              )}
            </div>

            {/* Add tags section */}
            {canAddTags && (
              <div className="space-y-4 border-t pt-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium">
                    Add Tags
                    {remainingSlots < limit && (
                      <span className="ml-2 text-xs text-muted-foreground">
                        ({remainingSlots} remaining)
                      </span>
                    )}
                  </h3>
                </div>

                {/* Quick add tags section */}
                <QuickAddTags
                  onTagSelect={handleQuickAddTag}
                  excludeTagIds={Array.from(assignedTagIds) as string[]}
                  limit={tagSettings?.quick_add_tags_limit ?? 7}
                  size="md"
                  showTitle={true}
                  disabled={isAssigning}
                />

                {/* Tag search and selection */}
                <div className="space-y-2">
                  <div className="text-xs font-medium text-muted-foreground">
                    Search or Create Tags
                  </div>
                  <TagTypeahead
                    selectedTags={selectedTags}
                    onTagsChange={setSelectedTags}
                    excludeTagIds={Array.from(assignedTagIds) as string[]}
                    maxTags={remainingSlots}
                    placeholder="Search tags or type to create new..."
                    size="md"
                    className="w-full"
                    onNewTagCreated={async (tag) => {
                      try {
                        await assignTags([tag.id]);
                      } catch (err) {
                        setError(err instanceof Error ? err.message : 'Failed to assign created tag');
                      }
                    }}
                  />
                </div>

                {/* Selected tags preview */}
                {availableSelectedTags.length > 0 && (
                  <div className="space-y-2">
                    <div className="text-xs text-muted-foreground">Selected to add:</div>
                    <div className="flex flex-wrap gap-1.5">
                      {availableSelectedTags.map((tag) => (
                        <div
                          key={tag.id}
                          className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-primary/10 text-primary text-xs"
                        >
                          <span>{tag.display_name || tag.name}</span>
                          <button
                            type="button"
                            onClick={() => setSelectedTags(prev => prev.filter(t => t.id !== tag.id))}
                            className="hover:bg-primary/20 rounded-full p-0.5 transition-colors"
                            aria-label={`Remove ${tag.display_name || tag.name} from selection`}
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Validation warnings */}
                {wouldExceedLimit && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      Cannot add {availableSelectedTags.length} tags. Only {remainingSlots} slot(s) remaining.
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            )}

            {/* Max tags reached message */}
            {!canAddTags && (
              <div className="text-sm text-muted-foreground py-6 text-center border-2 border-dashed border-muted rounded-lg">
                <Tag className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>Maximum of {limit} tags reached</p>
                <p className="text-xs mt-1">Remove a tag to add new ones</p>
              </div>
            )}
          </div>

          {/* Footer actions */}
          <div className="flex-shrink-0 flex items-center justify-end gap-3 pt-4 border-t p-6">
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isProcessing}
            >
              Close
            </Button>
            
            {canAddTags && availableSelectedTags.length > 0 && (
              <Button
                onClick={handleAssignTags}
                disabled={isProcessing || wouldExceedLimit || availableSelectedTags.length === 0}
                className="min-w-[120px]"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Adding...
                  </>
                ) : (
                  <>
                    <Plus className="h-4 w-4 mr-2" />
                    Add {availableSelectedTags.length} Tag{availableSelectedTags.length === 1 ? '' : 's'}
                  </>
                )}
              </Button>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Custom unassign confirmation modal */}
      <TagUnassignConfirmModal
        tag={unassignModal.tag}
        open={unassignModal.open}
        onOpenChange={(open) => setUnassignModal({ open, tag: unassignModal.tag })}
        onConfirm={handleUnassignConfirm}
        onCancel={handleUnassignCancel}
        loading={isUnassigning}
      />
    </>
  );
}

export default EditTagsModal;
