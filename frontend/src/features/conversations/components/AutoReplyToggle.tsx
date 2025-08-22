/**
 * Auto-reply toggle component for AI assistant.
 * Allows human agents to enable/disable AI automatic responses.
 */

import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { Switch } from '@/components/ui/Switch';
import { Badge } from '@/components/ui/Badge';
import { Bot, User } from 'lucide-react';
import { toast } from '@/components/feedback/Toast';
import { ConversationsApi } from '../api/conversationsApi';

interface AutoReplyToggleProps {
  conversationId: string;
  initialEnabled?: boolean;
  currentEnabled?: boolean; // Current state from parent
  className?: string;
}

interface ToggleAutoReplyRequest {
  conversation_id: string;
  enabled: boolean;
}

export function AutoReplyToggle({ 
  conversationId, 
  initialEnabled = true, 
  currentEnabled,
  className = "" 
}: AutoReplyToggleProps) {
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
    console.log(`🔄 [AUTO-REPLY] State sync:`, {
      conversationId,
      autoReplyStatus: autoReplyStatus?.ai_autoreply_enabled,
      currentEnabled,
      initialEnabled,
      actualEnabled,
      isEnabled
    });
    setIsEnabled(actualEnabled);
  }, [actualEnabled, conversationId, autoReplyStatus, currentEnabled, initialEnabled, isEnabled]);

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
    },
    onError: (error: Error, variables) => {
      // Revert optimistic update - go back to the previous state
      setIsEnabled(!variables.enabled);
      
      toast.error(`Failed to Update AI Assistant: ${error.message}`);
    },
  });

  const handleToggle = (enabled: boolean) => {
    toggleMutation.mutate({
      conversation_id: conversationId,
      enabled,
    });
  };

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Status Badge */}
      <Badge 
        variant={isEnabled ? "default" : "secondary"}
        className="flex items-center gap-1.5 px-2.5 py-1"
      >
        {isEnabled ? (
          <>
            <Bot className="w-3.5 h-3.5" />
            AI Assistant
          </>
        ) : (
          <>
            <User className="w-3.5 h-3.5" />
            Human Agent
          </>
        )}
      </Badge>

      {/* Toggle Switch */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">
          {isEnabled ? 'Auto-reply ON' : 'Auto-reply OFF'}
        </span>
        <Switch
          checked={isEnabled}
          onCheckedChange={(newState) => handleToggle(newState)}
          disabled={toggleMutation.isPending || isLoadingStatus}
          aria-label={`Toggle AI auto-reply ${isEnabled ? 'off' : 'on'}`}
        />
      </div>

      {/* Loading indicators */}
      {(toggleMutation.isPending || isLoadingStatus) && (
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-xs text-muted-foreground">
            {toggleMutation.isPending ? 'Updating...' : 'Loading...'}
          </span>
        </div>
      )}
    </div>
  );
}
