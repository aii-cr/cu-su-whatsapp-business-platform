/**
 * Auto-reply toggle component for AI assistant.
 * Allows human agents to enable/disable AI automatic responses.
 */

import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Switch } from '@/components/ui/Switch';
import { Badge } from '@/components/ui/Badge';
import { Bot, User } from 'lucide-react';
import { toast } from '@/hooks/useToast';
import { ConversationsApi } from '../api/conversationsApi';

interface AutoReplyToggleProps {
  conversationId: string;
  initialEnabled?: boolean;
  className?: string;
}

interface ToggleAutoReplyRequest {
  conversation_id: string;
  enabled: boolean;
}

export function AutoReplyToggle({ 
  conversationId, 
  initialEnabled = true, 
  className = "" 
}: AutoReplyToggleProps) {
  const [isEnabled, setIsEnabled] = useState(initialEnabled);
  const queryClient = useQueryClient();

  const toggleMutation = useMutation({
    mutationFn: async (request: ToggleAutoReplyRequest) => 
      ConversationsApi.toggleAIAutoReply(request.conversation_id, request.enabled),
    onMutate: async (variables) => {
      // Optimistic update
      setIsEnabled(variables.enabled);
    },
    onSuccess: (data) => {
      toast({
        title: data.data.ai_autoreply_enabled ? 'AI Assistant Enabled' : 'AI Assistant Disabled',
        description: data.data.ai_autoreply_enabled 
          ? 'AI will automatically respond to customer messages'
          : 'Human agents will handle all responses manually',
        variant: 'default',
      });

      // Invalidate conversation queries to update the conversation data
      queryClient.invalidateQueries({ 
        queryKey: ['conversation', conversationId] 
      });
    },
    onError: (error: Error, variables) => {
      // Revert optimistic update
      setIsEnabled(!variables.enabled);
      
      toast({
        title: 'Failed to Update AI Assistant',
        description: error.message,
        variant: 'destructive',
      });
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
          onCheckedChange={handleToggle}
          disabled={toggleMutation.isPending}
          aria-label={`Toggle AI auto-reply ${isEnabled ? 'off' : 'on'}`}
        />
      </div>

      {/* Loading indicator */}
      {toggleMutation.isPending && (
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-xs text-muted-foreground">Updating...</span>
        </div>
      )}
    </div>
  );
}
