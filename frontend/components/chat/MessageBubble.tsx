/**
 * WhatsApp-style message bubble component.
 * Displays individual messages with proper styling based on sender type.
 */

import * as React from 'react';
import { Message, SenderType, MessageStatus, MessageType } from '@/features/messages/models/message';
import { Avatar } from '@/components/ui/Avatar';
import { Badge } from '@/components/ui/Badge';
import { formatRelativeTime } from '@/lib/utils';
import { cn } from '@/lib/utils';
import { 
  CheckIcon, 
  ClockIcon,
  ExclamationTriangleIcon,
  DocumentIcon,
  PhotoIcon 
} from '@heroicons/react/24/outline';

export interface MessageBubbleProps {
  message: Message;
  isOwn?: boolean;
  showAvatar?: boolean;
  showTimestamp?: boolean;
  className?: string;
}

const MessageBubble = React.forwardRef<HTMLDivElement, MessageBubbleProps>(
  ({ message, isOwn = false, showAvatar = true, showTimestamp = true, className }, ref) => {
    const isSystem = message.sender_role === 'system';
    const isOutbound = message.direction === 'outbound'; // Agent message
    const isInbound = message.direction === 'inbound'; // Customer message
    
    // Override isOwn based on direction for correct alignment
    const shouldAlignRight = isOutbound; // Agent messages go right

    // Status icon and timestamp based on message status
    const StatusIcon = () => {
      // For outbound messages, show status
      if (!shouldAlignRight) return null;
      
      switch (message.status) {
        case 'pending':
          return <ClockIcon className="w-3 h-3 text-muted-foreground" />;
        case 'sent':
          return <CheckIcon className="w-3 h-3 text-muted-foreground" />;
        case 'delivered':
          return (
            <div className="flex">
              <CheckIcon className="w-3 h-3 text-muted-foreground -mr-1" />
              <CheckIcon className="w-3 h-3 text-muted-foreground" />
            </div>
          );
        case 'read':
          return (
            <div className="flex">
              <CheckIcon className="w-3 h-3 text-primary -mr-1" />
              <CheckIcon className="w-3 h-3 text-primary" />
            </div>
          );
        case 'failed':
          return <ExclamationTriangleIcon className="w-3 h-3 text-destructive" />;
        default:
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
            {message.text_content || message.content?.text}
          </Badge>
        </div>
      );
    }

    return (
      <div
        ref={ref}
        className={cn(
          'flex mb-4 group',
          shouldAlignRight ? 'justify-end' : 'justify-start',
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

        <div className={cn('max-w-xs lg:max-w-md', shouldAlignRight && showAvatar && 'mr-2')}>
          {/* Sender name for received messages */}
          {!shouldAlignRight && message.sender_name && (
            <p className="text-xs text-muted-foreground mb-1 ml-1">
              {message.sender_name}
            </p>
          )}

          {/* Message bubble */}
          <div
            className={cn(
              'relative px-4 py-2 rounded-lg shadow-sm',
              shouldAlignRight 
                ? 'bg-primary text-primary-foreground' // Agent messages - blue
                : 'bg-surface border border-border text-foreground', // Customer messages - surface color
              // WhatsApp-style bubble tail (optional)
              'before:absolute before:content-[""] before:w-0 before:h-0',
              shouldAlignRight
                ? 'before:right-[-6px] before:top-2 before:border-l-[6px] before:border-l-primary before:border-t-[6px] before:border-t-transparent before:border-b-[6px] before:border-b-transparent'
                : 'before:left-[-6px] before:top-2 before:border-r-[6px] before:border-r-surface before:border-t-[6px] before:border-t-transparent before:border-b-[6px] before:border-b-transparent'
            )}
          >
            {/* Media content */}
            {message.type !== 'text' && <MediaContent />}

            {/* Text content */}
            {message.text_content && (
              <p className={cn(
                'text-sm leading-relaxed',
                message.type !== 'text' && 'mt-2'
              )}>
                {message.text_content}
              </p>
            )}
            
            {/* Fallback for content object */}
            {!message.text_content && message.content?.text && (
              <p className={cn(
                'text-sm leading-relaxed',
                message.type !== 'text' && 'mt-2'
              )}>
                {message.content.text}
              </p>
            )}

            {/* Timestamp and status */}
            <div className={cn(
              'flex items-center justify-end mt-1 space-x-1',
              shouldAlignRight ? 'text-primary-foreground/70' : 'text-muted-foreground'
            )}>
              {showTimestamp && (
                <span className="text-xs">
                  {formatRelativeTime(getDisplayTimestamp())}
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
              fallback={message.sender_name?.charAt(0) || 'A'}
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