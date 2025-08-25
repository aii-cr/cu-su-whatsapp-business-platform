/**
 * Simple markdown display component for showing formatted text
 */

import React from 'react';
import { cn } from '@/lib/utils';
import styles from './Markdown.module.scss';

export interface MarkdownProps {
  content: string;
  className?: string;
}

export function Markdown({ content, className }: MarkdownProps) {
  // Simple markdown processing - for more complex needs, use a proper markdown parser
  const processMarkdown = (text: string) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
      .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic
      .replace(/`(.*?)`/g, '<code>$1</code>') // Inline code
      .replace(/\n/g, '<br>'); // Line breaks
  };

  return (
    <div 
      className={cn(styles.markdown, className)}
      dangerouslySetInnerHTML={{ __html: processMarkdown(content) }}
    />
  );
}
