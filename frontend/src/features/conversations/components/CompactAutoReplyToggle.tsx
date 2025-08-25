/**
 * Compact auto-reply toggle component for conversation list items.
 * A smaller version of AutoReplyToggle for use in conversation cards.
 */

import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { Switch } from '@/components/ui/Switch';
import { Bot, User } from 'lucide-react';
import { toast } from '@/components/feedback/Toast';
import { ConversationsApi } from '../api/conversationsApi';

interface CompactAutoReplyToggleProps {
  conversationId: string;
  initialEnabled?: boolean;
  currentEnabled?: boolean;
  className?: string;
}

interface ToggleAutoReplyRequest {
  conversation_id: string;
  enabled: boolean;
}

export function CompactAutoReplyToggle({ 
  conversationId, 
  initialEnabled = true, 
  currentEnabled,
  className = "" 
}: CompactAutoReplyToggleProps) {
  const queryClient = useQueryClient();

  // Fetch the current auto-reply status to ensure we have the latest state
  const { data: autoReplyStatus, error: statusError, isLoading: isLoadingStatus } = useQuery({
    queryKey: ['conversation-auto-reply', conversationId],
    queryFn: () => ConversationsApi.getAIAutoReplyStatus(conversationId),
    enabled: !!conversationId,
    staleTime: 0, // Always fetch fresh data
    refetchOnWindowFocus: true, // Refetch when window regains focus
    retry: 2, // Retry up to 2 times
    retryDelay: 1000, // Wait 1 second between retries
  });

  // Use the fetched status as the source of truth, fallback to props
  const actualEnabled = autoReplyStatus?.ai_autoreply_enabled ?? currentEnabled ?? initialEnabled;
  const [isEnabled, setIsEnabled] = useState(actualEnabled);

  // Update local state when any source changes
  useEffect(() => {
    setIsEnabled(actualEnabled);
  }, [actualEnabled, conversationId, autoReplyStatus, currentEnabled, initialEnabled]);

  const toggleMutation = useMutation({
    mutationFn: async (request: ToggleAutoReplyRequest) => 
      ConversationsApi.toggleAIAutoReply(request.conversation_id, request.enabled),
    onMutate: async (variables) => {
      // Optimistic update - set to the new state
      setIsEnabled(variables.enabled);
    },
    onSuccess: (data) => {
      // Invalidate both conversation and auto-reply status queries
      queryClient.invalidateQueries({ 
        queryKey: ['conversation', conversationId] 
      });
      queryClient.invalidateQueries({ 
        queryKey: ['conversation-auto-reply', conversationId] 
      });
      queryClient.invalidateQueries({ 
        queryKey: ['conversations', 'list'] 
      });
      
      // Show success toast
      const action = data.ai_autoreply_enabled ? 'enabled' : 'disabled';
      toast.success(`AI Auto-reply ${action} successfully`);
    },
    onError: (error: Error, variables) => {
      // Revert optimistic update - go back to the previous state
      setIsEnabled(!variables.enabled);
      
      toast.error(`Failed to Update AI Assistant: ${error.message}`);
    },
  });

  const handleToggle = (enabled: boolean, e?: React.MouseEvent) => {
    // Prevent event propagation to avoid triggering conversation click
    if (e) {
      e.stopPropagation();
    }
    
    toggleMutation.mutate({
      conversation_id: conversationId,
      enabled,
    });
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Status Icon */}
      <div className="flex items-center gap-1">
        {isEnabled ? (
          <Bot className="w-3 h-3 text-blue-500" />
        ) : (
          <User className="w-3 h-3 text-gray-400" />
        )}
      </div>
      
      {/* Context Text */}
      <span className="text-xs text-muted-foreground whitespace-nowrap">
        {isEnabled ? 'AI Agent Auto Reply' : 'Human Agent'}
      </span>
      
      {/* Compact Toggle Switch */}
      <Switch
        checked={isEnabled}
        onCheckedChange={(newState) => handleToggle(newState)}
        disabled={toggleMutation.isPending || isLoadingStatus}
        aria-label={`Toggle AI auto-reply ${isEnabled ? 'off' : 'on'}`}
        className="scale-75"
        onClick={(e) => e.stopPropagation()}
      />

      {/* Loading indicator */}
      {(toggleMutation.isPending || isLoadingStatus) && (
        <div className="w-3 h-3 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      )}
    </div>
  );
}
