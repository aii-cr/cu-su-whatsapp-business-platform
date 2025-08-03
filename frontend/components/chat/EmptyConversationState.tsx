/**
 * Empty state component for when no conversation is selected.
 * Shows a placeholder with instructions for starting a conversation.
 */

import * as React from 'react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { 
  ChatBubbleLeftRightIcon,
  PlusIcon,
  PhoneIcon,
  EnvelopeIcon 
} from '@heroicons/react/24/outline';

export interface EmptyConversationStateProps {
  onStartConversation?: () => void;
  className?: string;
}

const EmptyConversationState = React.forwardRef<HTMLDivElement, EmptyConversationStateProps>(
  ({ onStartConversation, className = '' }, ref) => {
    return (
      <div 
        ref={ref}
        className={`h-full flex items-center justify-center p-8 ${className}`}
      >
        <Card className="max-w-md">
          <CardContent className="p-8 text-center">
            <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-primary-500/10 flex items-center justify-center">
              <ChatBubbleLeftRightIcon className="w-12 h-12 text-primary-500" />
            </div>
            
            <h2 className="text-2xl font-semibold mb-4">
              Welcome to WhatsApp Business
            </h2>
            
            <p className="text-muted-foreground mb-6 leading-relaxed">
              Select a conversation from the sidebar to start chatting with your customers, 
              or create a new conversation to begin engaging with potential clients.
            </p>
            
            <div className="flex flex-col space-y-3">
              {onStartConversation && (
                <Button 
                  onClick={onStartConversation}
                  className="flex items-center justify-center"
                >
                  <PlusIcon className="w-5 h-5 mr-2" />
                  Start New Conversation
                </Button>
              )}
              
              <div className="flex space-x-3">
                <Button 
                  variant="outline" 
                  size="sm"
                  className="flex-1 flex items-center justify-center"
                >
                  <PhoneIcon className="w-4 h-4 mr-2" />
                  Quick Call
                </Button>
                
                <Button 
                  variant="outline" 
                  size="sm"
                  className="flex-1 flex items-center justify-center"
                >
                  <EnvelopeIcon className="w-4 h-4 mr-2" />
                  Send Email
                </Button>
              </div>
            </div>
            
            <div className="mt-8 pt-6 border-t border-border">
              <p className="text-xs text-muted-foreground">
                💡 <strong>Pro tip:</strong> Use keyboard shortcuts to navigate faster. 
                Press <kbd className="px-1 py-0.5 text-xs bg-muted rounded">Ctrl+K</kbd> to quickly search conversations.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }
);
EmptyConversationState.displayName = 'EmptyConversationState';

export { EmptyConversationState };