/**
 * WhatsApp-style message composer component.
 * Handles text input, file attachments, and message sending.
 */

import * as React from 'react';
import { useState, useRef } from 'react';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { cn } from '@/lib/utils';
import { 
  PaperAirplaneIcon,
  PaperClipIcon,
  FaceSmileIcon,
  MicrophoneIcon 
} from '@heroicons/react/24/outline';

export interface MessageComposerProps {
  onSendMessage: (text: string) => void;
  onSendMedia?: (file: File, caption?: string) => void;
  onTypingStart?: () => void;
  onTypingStop?: () => void;
  disabled?: boolean;
  loading?: boolean;
  placeholder?: string;
  maxLength?: number;
  className?: string;
}

const MessageComposer = React.forwardRef<HTMLDivElement, MessageComposerProps>(
  ({ 
    onSendMessage, 
    onSendMedia,
    onTypingStart,
    onTypingStop,
    disabled = false, 
    loading = false,
    placeholder = "Type a message...",
    maxLength = 4096,
    className 
  }, ref) => {
      const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Auto-resize textarea
    const adjustTextareaHeight = () => {
      const textarea = textareaRef.current;
      if (textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
      }
    };

    React.useEffect(() => {
      adjustTextareaHeight();
    }, [message]);

    const handleSend = () => {
      const trimmedMessage = message.trim();
      if (trimmedMessage && !disabled && !loading) {
        onSendMessage(trimmedMessage);
        setMessage('');
        onTypingStop?.(); // Stop typing indicator when sending
        // Reset textarea height
        if (textareaRef.current) {
          textareaRef.current.style.height = 'auto';
        }
      }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file && onSendMedia) {
        // For now, send without caption. In the future, we can show a preview dialog
        onSendMedia(file);
        // Reset file input
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const value = e.target.value;
      if (value.length <= maxLength) {
        const wasEmpty = message.length === 0;
        setMessage(value);
        
        // Send typing indicators
        if (wasEmpty && value.length > 0) {
          onTypingStart?.();
        } else if (!wasEmpty && value.length === 0) {
          onTypingStop?.();
        }
      }
    };

    return (
      <div 
        ref={ref}
        className={cn(
          'flex items-end space-x-2 p-4 bg-background border-t border-border',
          className
        )}
      >
        {/* File attachment button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || loading}
          className="h-10 w-10 rounded-full p-0 hover:bg-muted"
          aria-label="Attach file"
        >
          <PaperClipIcon className="w-5 h-5 text-muted-foreground" />
        </Button>

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*,video/*,audio/*,.pdf,.doc,.docx,.txt"
          onChange={handleFileChange}
          className="hidden"
        />

        {/* Message input area */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            disabled={disabled || loading}
            rows={1}
            className={cn(
              'w-full max-h-[120px] px-4 py-3 pr-12 text-sm resize-none',
              'bg-surface border border-border rounded-full',
              'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
              'placeholder:text-muted-foreground',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          />
          
          {/* Character count */}
          {message.length > maxLength * 0.8 && (
            <div className="absolute -top-6 right-0 text-xs text-muted-foreground">
              {message.length}/{maxLength}
            </div>
          )}

          {/* Emoji button (placeholder for future implementation) */}
          <Button
            variant="ghost"
            size="sm"
            disabled={disabled || loading}
            className="absolute right-2 top-1/2 transform -translate-y-1/2 h-8 w-8 rounded-full p-0 hover:bg-muted/50"
            aria-label="Add emoji"
          >
            <FaceSmileIcon className="w-4 h-4 text-muted-foreground" />
          </Button>
        </div>

        {/* Send button or voice note button */}
        {message.trim() ? (
          <Button
            onClick={handleSend}
            disabled={disabled || loading || !message.trim()}
            className="h-10 w-10 rounded-full p-0 bg-primary hover:bg-primary/90 text-primary-foreground"
            aria-label="Send message"
          >
            {loading ? (
              <LoadingSpinner size="sm" className="text-primary-foreground" />
            ) : (
              <PaperAirplaneIcon className="w-5 h-5" />
            )}
          </Button>
        ) : (
          <Button
            variant="ghost"
            size="sm"
            disabled={disabled || loading}
            className="h-10 w-10 rounded-full p-0 hover:bg-accent"
            aria-label="Voice message"
          >
            <MicrophoneIcon className="w-5 h-5 text-muted-foreground" />
          </Button>
        )}
      </div>
    );
  }
);
MessageComposer.displayName = 'MessageComposer';

export { MessageComposer };