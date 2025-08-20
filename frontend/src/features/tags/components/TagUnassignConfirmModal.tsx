/**
 * TagUnassignConfirmModal component - custom confirmation modal for tag unassignment
 * Replaces the default JavaScript confirm dialog with a styled modal
 */

import * as React from 'react';
import { AlertTriangle, X, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/Dialog';
import { Button } from '@/components/ui/Button/index';
import { TagSummary } from '../models/tag';

export interface TagUnassignConfirmModalProps {
  tag: TagSummary | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => Promise<void>;
  onCancel: () => void;
  className?: string;
  loading?: boolean;
}

export function TagUnassignConfirmModal({
  tag,
  open,
  onOpenChange,
  onConfirm,
  onCancel,
  className,
  loading = false,
}: TagUnassignConfirmModalProps) {
  const [isProcessing, setIsProcessing] = React.useState(false);

  const handleConfirm = React.useCallback(() => {
    if (isProcessing || loading) return;
    
    // Immediately disable the button and show loading
    setIsProcessing(true);
    
    // Call the async function and handle the result
    onConfirm()
      .then(() => {
        // Success: close the modal
        onOpenChange(false);
      })
      .catch((error: unknown) => {
        // Error: keep modal open, let parent handle error display
        console.error('Error during tag unassignment:', error);
      })
      .finally(() => {
        // Always reset processing state
        setIsProcessing(false);
      });
  }, [onConfirm, onOpenChange, isProcessing, loading]);

  const handleCancel = React.useCallback(() => {
    if (isProcessing || loading) return;
    
    onCancel();
    onOpenChange(false);
  }, [onCancel, onOpenChange, isProcessing, loading]);

  // Don't render if tag is null
  if (!tag) {
    return null;
  }

  const isDisabled = isProcessing || loading;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent 
        className={cn(
          'sm:max-w-md w-full max-h-[95vh] overflow-hidden flex flex-col relative z-[1000]',
          className
        )}
      >
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-warning/10">
              <AlertTriangle className="h-5 w-5 text-warning" />
            </div>
            <span>Unassign Tag</span>
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 flex flex-col space-y-4 p-6">
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Are you sure you want to unassign the tag from this conversation?
            </p>
            
            {/* Tag preview */}
            <div className="flex items-center gap-2 p-3 rounded-lg border bg-muted/30">
              <div 
                className="w-3 h-3 rounded-full flex-shrink-0"
                style={{ backgroundColor: tag.color }}
              />
              <span className="font-medium text-sm">
                {tag.display_name || tag.name}
              </span>
              {tag.category && (
                <span className="text-xs text-muted-foreground capitalize">
                  • {tag.category}
                </span>
              )}
            </div>
            
            <p className="text-xs text-muted-foreground">
              This action can be undone by reassigning the tag later.
            </p>
          </div>
        </div>

        {/* Footer actions */}
        <div className="flex-shrink-0 flex items-center justify-end gap-3 pt-4 border-t p-6">
          <Button
            variant="outline"
            onClick={handleCancel}
            disabled={isDisabled}
            className="flex items-center gap-2"
          >
            <X className="h-4 w-4" />
            Cancel
          </Button>
          
          <Button
            variant="destructive"
            onClick={handleConfirm}
            disabled={isDisabled}
            className="flex items-center gap-2 min-w-[120px]"
          >
            {isProcessing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Unassigning...
              </>
            ) : (
              <>
                <AlertTriangle className="h-4 w-4" />
                Unassign Tag
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default TagUnassignConfirmModal;
