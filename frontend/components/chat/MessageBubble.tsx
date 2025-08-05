/**
 * WhatsApp-style message bubble component.
 * Displays individual messages with proper styling based on sender type.
 */

import * as React from 'react';
import { Message, SenderType, MessageStatus, MessageType } from '@/features/messages/models/message';
import { Avatar } from '@/components/ui/Avatar';
import { Badge } from '@/components/ui/Badge';
import { formatMessageTime, cn } from '@/lib/utils';
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
      
      const iconClass = shouldAlignRight ? 'text-white/90' : 'text-slate-500 dark:text-slate-400';
      const readIconClass = shouldAlignRight ? 'text-white' : 'text-blue-500';
      const failedIconClass = shouldAlignRight ? 'text-red-200' : 'text-red-500';
      
      switch (message.status) {
        case 'sending':
          return (
            <div className="flex items-center">
              <ClockIcon className={`w-3 h-3 ${iconClass} animate-pulse`} />
            </div>
          );
        case 'pending':
          return <ClockIcon className={`w-3 h-3 ${iconClass}`} />;
        case 'sent':
          return <CheckIcon className={`w-3 h-3 ${iconClass}`} />;
        case 'delivered':
          return (
            <div className="flex">
              <CheckIcon className={`w-3 h-3 ${iconClass} -mr-1`} />
              <CheckIcon className={`w-3 h-3 ${iconClass}`} />
            </div>
          );
        case 'read':
          return (
            <div className="flex">
              <CheckIcon className={`w-3 h-3 ${readIconClass} -mr-1`} />
              <CheckIcon className={`w-3 h-3 ${readIconClass}`} />
            </div>
          );
        case 'failed':
          return <ExclamationTriangleIcon className={`w-3 h-3 ${failedIconClass}`} />;
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

        <div className={cn('max-w-sm lg:max-w-lg xl:max-w-xl', shouldAlignRight && showAvatar && 'mr-2')}>
          {/* Sender name for received messages */}
          {!shouldAlignRight && message.sender_name && (
            <p className="text-xs text-muted-foreground mb-1 ml-1">
              {message.sender_name}
            </p>
          )}
          
          {/* Sender info for outbound business messages */}
          {shouldAlignRight && message.direction === 'outbound' && message.sender_name && (
            <p className="text-xs text-muted-foreground mb-1 text-right mr-1">
              Sent by {message.sender_name}
            </p>
          )}

          {/* Message bubble */}
          <div
            className={cn(
              'relative px-4 py-2 rounded-lg shadow-sm',
              shouldAlignRight 
                ? 'bg-blue-500 text-white' // Agent messages - solid blue with white text for better contrast
                : 'bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-slate-900 dark:text-slate-100', // Customer messages with better contrast
              // WhatsApp-style bubble tail (optional)
              'before:absolute before:content-[""] before:w-0 before:h-0',
              shouldAlignRight
                ? 'before:right-[-6px] before:top-2 before:border-l-[6px] before:border-l-blue-500 before:border-t-[6px] before:border-t-transparent before:border-b-[6px] before:border-b-transparent'
                : 'before:left-[-6px] before:top-2 before:border-r-[6px] before:border-r-white dark:before:border-r-slate-700 before:border-t-[6px] before:border-t-transparent before:border-b-[6px] before:border-b-transparent'
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
              shouldAlignRight ? 'text-white/90' : 'text-slate-500 dark:text-slate-400'
            )}>
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