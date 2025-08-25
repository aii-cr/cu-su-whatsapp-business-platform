/**
 * WhatsApp-style message bubble component.
 * Displays individual messages with proper styling based on sender type.
 */

import * as React from 'react';
import { useState, useEffect } from 'react';
import { Message, SenderType, MessageStatus, MessageType } from '@/features/messages/models/message';
import { Avatar } from '@/components/ui/Avatar';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';
import { formatMessageTime } from '@/lib/timezone';
import { 
  CheckIcon, 
  ClockIcon,
  ExclamationTriangleIcon,
  DocumentIcon,
  PhotoIcon 
} from '@heroicons/react/24/outline';

// Simple markdown renderer for WhatsApp-style formatting
const renderMarkdown = (text: string): React.ReactNode => {
  if (!text) return null;
  
  // Split by lines to handle line breaks
  const lines = text.split('\n');
  
  return lines.map((line, lineIndex) => {
    // For empty lines, render a line break
    if (line.trim() === '') {
      return <br key={lineIndex} />;
    }
    
    // Handle bullet points
    if (line.trim().startsWith('• ')) {
      return (
        <div key={lineIndex} className="flex items-start space-x-2 mb-1">
          <span className="text-lg leading-none mt-0.5">•</span>
          <span className="flex-1">{line.trim().substring(2)}</span>
        </div>
      );
    }
    
    // Handle numbered lists (simple detection)
    const numberedMatch = line.trim().match(/^(\d+)\.\s+(.+)$/);
    if (numberedMatch) {
      return (
        <div key={lineIndex} className="flex items-start space-x-2 mb-1">
          <span className="text-sm font-medium leading-none mt-0.5">{numberedMatch[1]}.</span>
          <span className="flex-1">{numberedMatch[2]}</span>
        </div>
      );
    }
    
    // Handle bold text (simple **text** detection)
    if (line.includes('**')) {
      const parts = line.split(/(\*\*[^*]+\*\*)/g);
      return (
        <div key={lineIndex} className="mb-1">
          {parts.map((part, partIndex) => {
            if (part.startsWith('**') && part.endsWith('**')) {
              return (
                <strong key={partIndex} className="font-semibold">
                  {part.slice(2, -2)}
                </strong>
              );
            }
            return part;
          })}
        </div>
      );
    }
    
    // Regular line - render as a block to preserve line breaks
    return <div key={lineIndex} className="mb-1">{line}</div>;
  });
};

// AI Indicator component
const AIIndicator = () => (
  <div className="flex items-center space-x-1 text-xs text-blue-100/90 mb-1">
    <span role="img" aria-label="robot" className="text-sm">{'🤖'}</span>
    <span className="font-medium">AI Agent</span>
  </div>
);

export interface MessageBubbleProps {
  message: Message;
  isOwn?: boolean;
  showAvatar?: boolean;
  showTimestamp?: boolean;
  className?: string;
  isOptimistic?: boolean;
  isNewMessage?: boolean;
  onRetry?: (message: Message) => void;
}

const MessageBubble = React.forwardRef<HTMLDivElement, MessageBubbleProps>(
  ({ message, isOwn = false, showAvatar = true, showTimestamp = true, className, isOptimistic = false, isNewMessage = false, onRetry }, ref) => {
    // Track status changes for animation
    const [previousStatus, setPreviousStatus] = useState(message.status);
    const [shouldAnimateStatus, setShouldAnimateStatus] = useState(false);
    
    // Check if status changed and trigger animation
    useEffect(() => {
      if (message.status !== previousStatus) {
        console.log(`🔄 [MESSAGE_BUBBLE] Status changed for message ${message._id}: ${previousStatus} -> ${message.status}`);
        console.log(`🔄 [MESSAGE_BUBBLE] Message direction: ${message.direction}, sender_role: ${message.sender_role}`);
        console.log(`🔄 [MESSAGE_BUBBLE] Should show status: ${message.direction === 'outbound'}`);
        
        setShouldAnimateStatus(true);
        setPreviousStatus(message.status);
        
        // Remove animation flag after animation completes
        const timer = setTimeout(() => {
          setShouldAnimateStatus(false);
        }, 500); // Increased animation duration for better visibility
        
        return () => clearTimeout(timer);
      }
    }, [message.status, previousStatus, message._id, message.direction, message.sender_role]);
    
    // Log initial status for debugging
    useEffect(() => {
      if (message.direction === 'outbound') {
        console.log(`🔍 [MESSAGE_BUBBLE] Initial status for outbound message ${message._id}: ${message.status}`);
        console.log(`🔍 [MESSAGE_BUBBLE] Full message data:`, {
          _id: message._id,
          status: message.status,
          direction: message.direction,
          sender_role: message.sender_role,
          sent_at: message.sent_at,
          delivered_at: message.delivered_at,
          read_at: message.read_at,
          timestamp: message.timestamp
        });
      }
    }, [message._id, message.status, message.direction, message.sender_role, message.sent_at, message.delivered_at, message.read_at, message.timestamp]);
    
    const isSystem = message.sender_role === 'system';
    const isOutbound = message.direction === 'outbound'; // Agent message
    const isInbound = message.direction === 'inbound'; // Customer message
    const isAI = message.sender_role === 'ai_assistant' || message.is_automated; // AI assistant message
    
    // Debug logging for AI messages
    if (isOutbound) {
      console.log(`🔍 [MESSAGE_BUBBLE] Message ${message._id}:`, {
        sender_role: message.sender_role,
        is_automated: message.is_automated,
        isAI: isAI,
        direction: message.direction
      });
    }

    // Override isOwn based on direction for correct alignment
    const shouldAlignRight = isOutbound; // Agent messages go right

    // Status icon and timestamp based on message status
    const StatusIcon = () => {
      // Only show status for outbound messages (agent/AI messages)
      if (!shouldAlignRight) return null;
      
      const iconClass = 'text-white/70';
      const readIconClass = 'text-blue-300';
      const failedIconClass = 'text-red-300';
      
      console.log(`🔍 [STATUS_ICON] Message ${message._id} status: ${message.status}, direction: ${message.direction}, sender_role: ${message.sender_role}`);
      console.log(`🔍 [STATUS_ICON] Message should align right: ${shouldAlignRight}`);
      console.log(`🔍 [STATUS_ICON] Message is outbound: ${isOutbound}`);
      console.log(`🔍 [STATUS_ICON] Status field type: ${typeof message.status}, value: "${message.status}"`);
      
      switch (message.status) {
        case 'sending':
          console.log(`⏳ [STATUS_ICON] Showing sending status for message ${message._id}`);
          return (
            <div className="flex items-center">
              <ClockIcon className={`w-3 h-3 ${iconClass} animate-pulse`} />
            </div>
          );
        case 'sent':
          console.log(`📤 [STATUS_ICON] Showing sent status (single check) for message ${message._id}`);
          return (
            <div className={cn('flex items-center', getAnimationClass())}>
              <CheckIcon className={`w-3 h-3 ${iconClass}`} />
            </div>
          );
        case 'delivered':
          console.log(`✅ [STATUS_ICON] Showing delivered status (double check) for message ${message._id}`);
          return (
            <div className={cn('flex', getAnimationClass())}>
              <CheckIcon className={`w-3 h-3 ${iconClass} -mr-1`} />
              <CheckIcon className={`w-3 h-3 ${iconClass}`} />
            </div>
          );
        case 'read':
          console.log(`👁️ [STATUS_ICON] Showing read status (blue double check) for message ${message._id}`);
          return (
            <div className={cn('flex', getAnimationClass())}>
              <CheckIcon className={`w-3 h-3 ${readIconClass} -mr-1`} />
              <CheckIcon className={`w-3 h-3 ${readIconClass}`} />
            </div>
          );
        case 'failed':
          console.log(`❌ [STATUS_ICON] Showing failed status for message ${message._id}`);
          return <ExclamationTriangleIcon className={`w-3 h-3 ${failedIconClass}`} />;
        default:
          console.log(`❓ [STATUS_ICON] Unknown status "${message.status}" for message ${message._id}`);
          console.log(`❓ [STATUS_ICON] Available status values: sending, sent, delivered, read, failed`);
          return null;
      }
    };

    // Get the appropriate timestamp for display
    const getDisplayTimestamp = () => {
      if (message.status === 'read' && message.read_at) {
        return message.read_at;
      }
      if (message.status === 'delivered' && message.delivered_at) {
        return message.delivered_at;
      }
      if (message.status === 'sent' && message.sent_at) {
        return message.sent_at;
      }
      return message.timestamp;
    };

    // Media content renderer
    const MediaContent = () => {
      if (message.type === 'image') {
        return (
          <div className="relative">
            {(message.media_url || message.content?.media_url) ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={message.media_url || message.content?.media_url}
                alt={message.content?.caption || 'Image'}
                className="rounded-lg max-w-xs max-h-64 object-cover"
              />
            ) : (
              <div className="flex items-center justify-center w-48 h-32 bg-muted rounded-lg">
                <PhotoIcon className="w-8 h-8 text-muted-foreground" />
              </div>
            )}
            {message.content?.caption && (
              <p className="mt-2 text-sm">{message.content.caption}</p>
            )}
          </div>
        );
      }

      if (message.type === 'document') {
        return (
          <div className="flex items-center space-x-3 p-3 bg-muted rounded-lg max-w-xs">
            <DocumentIcon className="w-8 h-8 text-primary flex-shrink-0" />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium truncate">
                {message.content?.file_name || 'Document'}
              </p>
              {message.content?.file_size && (
                <p className="text-xs text-muted-foreground">
                  {(message.content.file_size / 1024 / 1024).toFixed(2)} MB
                </p>
              )}
            </div>
          </div>
        );
      }

      return null;
    };

    // System message (centered)
    if (isSystem) {
      return (
        <div ref={ref} className={cn('flex justify-center my-4', className)}>
          <Badge variant="secondary" className="text-xs px-3 py-1">
            {renderMarkdown(message.text_content || message.content?.text || '')}
          </Badge>
        </div>
      );
    }

    // Determine animation class based on message type and state
    const getAnimationClass = () => {
      if (isOptimistic) return 'animate-message-push-in';
      if (isNewMessage) {
        return shouldAlignRight ? 'animate-outbound-message' : 'animate-inbound-message';
      }
      return '';
    };

    return (
      <div
        ref={ref}
        className={cn(
          'flex mb-4 group message-animation-wrapper',
          shouldAlignRight ? 'justify-end' : 'justify-start',
          getAnimationClass(),
          className
        )}
      >
        {/* Avatar for received messages (customers - left side) */}
        {!shouldAlignRight && showAvatar && (
          <div className="mr-2 flex-shrink-0">
            <Avatar
              size="sm"
              fallback={message.sender_name?.charAt(0) || 'C'}
              className="mt-1"
            />
          </div>
        )}

        <div className={cn('max-w-sm lg:max-w-lg xl:max-w-xl', shouldAlignRight && showAvatar && 'mr-2')}>
          {/* Sender name for received messages */}
          {!shouldAlignRight && message.sender_name && (
            <p className="text-xs text-muted-foreground mb-1 ml-1">
              {message.sender_name}
            </p>
          )}
          
          {/* Sender info for outbound business messages */}
          {shouldAlignRight && message.direction === 'outbound' && message.sender_name && !isAI && (
            <p className="text-xs text-muted-foreground mb-1 text-right mr-1">
              Sent by {message.sender_name}
            </p>
          )}

          {/* AI Indicator for AI messages */}
          {isAI && shouldAlignRight && (
            <div className="text-right mr-1 mb-1">
              <AIIndicator />
            </div>
          )}

          {/* Message bubble */}
          <div
            className={cn(
              'relative px-4 py-2 rounded-lg shadow-sm message-bubble-animate',
              shouldAlignRight 
                ? 'bg-blue-500 text-white' // Agent messages - solid blue with white text for better contrast
                : 'bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-slate-900 dark:text-slate-100', // Customer messages with better contrast
              // WhatsApp-style bubble tail (optional)
              'before:absolute before:content-[""] before:w-0 before:h-0',
              shouldAlignRight
                ? 'before:right-[-6px] before:top-2 before:border-l-[6px] before:border-l-blue-500 before:border-t-[6px] before:border-t-transparent before:border-b-[6px] before:border-b-transparent'
                : 'before:left-[-6px] before:top-2 before:border-r-[6px] before:border-r-white dark:before:border-r-slate-700 before:border-t-[6px] before:border-t-transparent before:border-b-[6px] before:border-b-transparent',
              // Animation states
              {
                'optimistic': isOptimistic,
                'new-message': isNewMessage,
                'status-updating': message.status === 'delivered' || message.status === 'read'
              }
            )}
          >
            {/* Template message content */}
            {message.type === 'template' && message.template_data && (
              <div className="space-y-3">
                {/* Template Header (optional) */}
                {message.template_data.rendered_content?.header && (
                  <div className={cn(
                    "text-sm font-medium pb-2 border-b",
                    shouldAlignRight ? "border-white/20" : "border-slate-200 dark:border-slate-600"
                  )}>
                    {renderMarkdown(message.template_data.rendered_content.header)}
                  </div>
                )}
                
                {/* Template Body */}
                {message.template_data.rendered_content?.body && (
                  <div className="text-sm leading-relaxed">
                    {renderMarkdown(message.template_data.rendered_content.body)}
                  </div>
                )}
                
                {/* Template Footer (optional) */}
                {message.template_data.rendered_content?.footer && (
                  <div className={cn(
                    "text-xs opacity-75 pt-2 border-t",
                    shouldAlignRight ? "border-white/20" : "border-slate-200 dark:border-slate-600"
                  )}>
                    {message.template_data.rendered_content.footer}
                  </div>
                )}
                
                {/* Template Name Badge */}
                <div className="flex justify-end mt-2">
                  <Badge variant="secondary" className={cn(
                    "text-xs",
                    shouldAlignRight 
                      ? "bg-white/20 text-white border-white/30" 
                      : "bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-700 dark:text-slate-300 dark:border-slate-600"
                  )}>
                    📄 {message.template_data.name}
                  </Badge>
                </div>
              </div>
            )}

            {/* Media content */}
            {message.type !== 'text' && message.type !== 'template' && <MediaContent />}

            {/* Text content */}
            {message.type === 'text' && message.text_content && (
              <div className="text-sm leading-relaxed">
                {renderMarkdown(message.text_content)}
              </div>
            )}
            
            {/* Fallback for content object */}
            {message.type === 'text' && !message.text_content && message.content?.text && (
              <div className="text-sm leading-relaxed">
                {renderMarkdown(message.content.text)}
              </div>
            )}

            {/* Timestamp and status */}
            <div className={cn(
              'flex items-center justify-end mt-1 space-x-1',
              shouldAlignRight ? 'text-white/90' : 'text-slate-500 dark:text-slate-400'
            )}>
              {/* Retry button for failed messages */}
              {message.status === 'failed' && onRetry && shouldAlignRight && (
                <button
                  onClick={() => onRetry(message)}
                  className={cn(
                    'text-xs px-2 py-1 rounded bg-white/20 hover:bg-white/30 transition-colors',
                    'text-white/90 hover:text-white font-medium'
                  )}
                  title="Retry sending message"
                >
                  Retry
                </button>
              )}
              {showTimestamp && (
                <span className="text-xs font-medium">
                  {formatMessageTime(getDisplayTimestamp())}
                </span>
              )}
              <StatusIcon />
            </div>
          </div>
        </div>

        {/* Avatar for sent messages (agents - right side) */}
        {shouldAlignRight && showAvatar && (
          <div className="ml-2 flex-shrink-0">
            <Avatar
              size="sm"
              fallback={isAI ? '✨' : (message.sender_name?.charAt(0) || 'A')}
              className="mt-1"
            />
          </div>
        )}
      </div>
    );
  }
);
MessageBubble.displayName = 'MessageBubble';

export { MessageBubble };