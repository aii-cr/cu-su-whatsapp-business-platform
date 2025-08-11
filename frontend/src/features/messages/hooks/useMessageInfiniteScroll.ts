/**
 * Hook for managing infinite scroll and "load older messages" functionality.
 * Handles proper scrolling behavior when loading historical messages.
 */

import { useCallback, useRef } from 'react';
import { useMessages } from './useMessages';

interface UseMessageInfiniteScrollProps {
  conversationId: string;
  limit?: number;
}

export function useInfiniteMessages({
  conversationId,
  limit = 50,
}: UseMessageInfiniteScrollProps) {
  const messagesQuery = useMessages(conversationId, limit);
  const previousScrollHeight = useRef<number>(0);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Flatten all messages from all pages into a single array
  // Since backend now returns messages in DESC order (newest first),
  // we need to reverse each page but keep the overall order
  const allMessages = messagesQuery.data?.pages.flatMap(page => page.messages) || [];

  const handleLoadOlderMessages = useCallback(async () => {
    const container = messagesContainerRef.current;
    if (!container || !messagesQuery.hasNextPage || messagesQuery.isFetchingNextPage) {
      return;
    }

    // Store current scroll position and total height
    const scrollTop = container.scrollTop;
    const scrollHeight = container.scrollHeight;
    
    await messagesQuery.fetchNextPage();
    
    // After loading older messages, maintain the user's visual position
    // The new messages will be added above, so we need to adjust scroll
    requestAnimationFrame(() => {
      if (container) {
        const newScrollHeight = container.scrollHeight;
        const heightDifference = newScrollHeight - scrollHeight;
        // Adjust scroll position to maintain visual continuity
        container.scrollTop = scrollTop + heightDifference;
      }
    });
  }, [messagesQuery]);

  const scrollToBottom = useCallback((smooth = true) => {
    const container = messagesContainerRef.current;
    if (!container) return;

    container.scrollTo({
      top: container.scrollHeight,
      behavior: smooth ? 'smooth' : 'auto',
    });
  }, []);

  const isNearBottom = useCallback(() => {
    const container = messagesContainerRef.current;
    if (!container) return false;

    const threshold = 100; // pixels from bottom
    return container.scrollTop + container.clientHeight >= container.scrollHeight - threshold;
  }, []);

  return {
    // Messages data
    messages: allMessages,
    isLoading: messagesQuery.isLoading,
    error: messagesQuery.error,
    
    // Pagination
    hasNextPage: messagesQuery.hasNextPage,
    isFetchingNextPage: messagesQuery.isFetchingNextPage,
    fetchNextPage: messagesQuery.fetchNextPage,
    handleLoadOlderMessages,
    
    // Scroll management
    messagesContainerRef,
    scrollToBottom,
    isNearBottom,
    
    // Query controls
    refetch: messagesQuery.refetch,
    invalidate: () => messagesQuery.refetch(),
  };
}