/**
 * Conversation Context Component
 * Displays AI conversation memory and context information
 */

'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/feedback/LoadingSpinner';
import { useConversationContext } from '@/features/conversations/hooks/useConversationContext';
import { 
  BrainIcon, 
  ClockIcon, 
  ChatBubbleLeftRightIcon,
  TrashIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';

interface ConversationContextProps {
  conversationId: string;
  className?: string;
}

interface ConversationContext {
  conversation_id: string;
  history: Array<{
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    message_id: string;
  }>;
  summary: string;
  session_data: Record<string, any>;
  last_activity?: string;
  memory_size: number;
}

export const ConversationContext: React.FC<ConversationContextProps> = ({
  conversationId,
  className = ''
}) => {
  const { context, loading, error, refreshContext, clearMemory, isClearing } = useConversationContext(conversationId);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleClearMemory = async () => {
    if (!confirm('Are you sure you want to clear the AI memory for this conversation? This will reset the conversation context.')) {
      return;
    }
    
    await clearMemory();
  };

  if (loading && !context) {
    return (
      <Card className={`${className}`}>
        <CardContent className="p-4">
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner size="sm" text="Loading context..." />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={`${className}`}>
        <CardContent className="p-4">
          <div className="flex items-center space-x-2 text-error">
            <InformationCircleIcon className="w-5 h-5" />
            <span className="text-sm">{error}</span>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={refreshContext}
              className="ml-auto"
            >
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!context) {
    return null;
  }

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleTimeString();
    } catch {
      return 'Unknown';
    }
  };

  const getIntentFromContent = (content: string): string => {
    const lowerContent = content.toLowerCase();
    if (lowerContent.includes('reserva') || lowerContent.includes('booking')) return 'booking';
    if (lowerContent.includes('pago') || lowerContent.includes('payment')) return 'payment';
    if (lowerContent.includes('precio') || lowerContent.includes('price')) return 'pricing';
    if (lowerContent.includes('horario') || lowerContent.includes('schedule')) return 'scheduling';
    return 'general';
  };

  return (
    <Card className={`${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <BrainIcon className="w-5 h-5 text-primary" />
            <CardTitle className="text-lg">AI Context</CardTitle>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className="text-xs">
              {context.memory_size} messages
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? 'Collapse' : 'Expand'}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleClearMemory}
              disabled={isClearing}
              className="text-error hover:text-error"
            >
              <TrashIcon className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Summary */}
        {context.summary && (
          <div className="space-y-2">
            <div className="flex items-center space-x-2 text-sm font-medium">
              <ChatBubbleLeftRightIcon className="w-4 h-4" />
              <span>Conversation Summary</span>
            </div>
            <p className="text-sm text-muted-foreground bg-muted p-2 rounded">
              {context.summary}
            </p>
          </div>
        )}

        {/* Last Activity */}
        {context.last_activity && (
          <div className="flex items-center space-x-2 text-sm text-muted-foreground">
            <ClockIcon className="w-4 h-4" />
            <span>Last activity: {formatTimestamp(context.last_activity)}</span>
          </div>
        )}

        {/* Session Data */}
        {Object.keys(context.session_data).length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-medium">Session Data</div>
            <div className="text-xs space-y-1">
              {Object.entries(context.session_data).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-muted-foreground">{key}:</span>
                  <span>{String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Conversation History (Expandable) */}
        {isExpanded && context.history.length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-medium">Recent History</div>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {context.history.slice(-6).map((message, index) => (
                <div 
                  key={`${message.message_id}-${index}`}
                  className={`p-2 rounded text-xs ${
                    message.role === 'user' 
                      ? 'bg-primary/10 border-l-2 border-primary' 
                      : 'bg-muted border-l-2 border-muted-foreground'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <Badge 
                      variant={message.role === 'user' ? 'default' : 'secondary'}
                      className="text-xs"
                    >
                      {message.role === 'user' ? 'User' : 'AI'}
                    </Badge>
                    <span className="text-muted-foreground text-xs">
                      {formatTimestamp(message.timestamp)}
                    </span>
                  </div>
                  <p className="text-xs line-clamp-2">
                    {message.content}
                  </p>
                  {message.role === 'user' && (
                    <div className="mt-1">
                      <Badge 
                        variant="outline" 
                        className="text-xs"
                      >
                        {getIntentFromContent(message.content)}
                      </Badge>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {context.history.length === 0 && (
          <div className="text-center py-4 text-muted-foreground">
            <ChatBubbleLeftRightIcon className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No conversation history yet</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
