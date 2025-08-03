/**
 * Enhanced WebSocket client with conversation-specific messaging support.
 * Extends the base WebSocket client with real-time messaging capabilities.
 */

import { WebSocketClient } from './ws';
import { useAuthStore } from './store';
import { useQueryClient } from '@tanstack/react-query';
import { messageQueryKeys } from '@/features/messages/hooks/useMessages';
import { conversationQueryKeys } from '@/features/conversations/hooks/useConversations';
import { toast } from '@/components/ui/Toast';

// WebSocket message types for real-time messaging
export interface WebSocketMessageData {
  // New message received
  new_message: {
    conversation_id: string;
    message: Record<string, unknown>; // Message object
  };
  
  // Message status update
  message_status: {
    conversation_id: string;
    message_id: string;
    status: 'sent' | 'delivered' | 'read' | 'failed';
    timestamp: string;
  };
  
  // Conversation update
  conversation_update: {
    conversation_id: string;
    changes: Record<string, unknown>;
  };
  
  // New conversation created
  new_conversation: {
    conversation: Record<string, unknown>; // Conversation object
  };
  
  // User activity (typing, online/offline)
  user_activity: {
    conversation_id: string;
    user_id: string;
    user_name: string;
    activity: 'typing_start' | 'typing_stop' | 'online' | 'offline';
    timestamp: string;
  };
}

export class MessagingWebSocketClient extends WebSocketClient {
  private queryClient: ReturnType<typeof useQueryClient>;
  private subscriptions = new Set<string>();

  constructor(queryClient: ReturnType<typeof useQueryClient>) {
    super();
    this.queryClient = queryClient;
  }

  /**
   * Subscribe to a conversation for real-time updates
   */
  subscribeToConversation(conversationId: string) {
    if (this.subscriptions.has(conversationId)) {
      return; // Already subscribed
    }

    this.subscriptions.add(conversationId);
    this.send({
      type: 'subscribe_conversation',
      conversation_id: conversationId,
    });
  }

  /**
   * Unsubscribe from a conversation
   */
  unsubscribeFromConversation(conversationId: string) {
    if (!this.subscriptions.has(conversationId)) {
      return; // Not subscribed
    }

    this.subscriptions.delete(conversationId);
    this.send({
      type: 'unsubscribe_conversation',
      conversation_id: conversationId,
    });
  }

  /**
   * Send typing indicator
   */
  sendTypingIndicator(conversationId: string, isTyping: boolean) {
    this.send({
      type: isTyping ? 'typing_start' : 'typing_stop',
      conversation_id: conversationId,
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Handle incoming WebSocket messages
   */
  protected handleIncomingMessage(event: MessageEvent) {
    try {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'new_message':
          this.handleNewMessage(data.data || data);
          break;
          
        case 'message_status':
          this.handleMessageStatus(data.data || data);
          break;
          
        case 'conversation_update':
          this.handleConversationUpdate(data.data || data);
          break;
          
        case 'new_conversation':
          this.handleNewConversation(data.data || data);
          break;
          
        case 'user_activity':
          this.handleUserActivity(data.data || data);
          break;
          
        default:
          console.log('Unknown WebSocket message type:', data.type);
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error);
    }
  }

  private handleNewMessage(data: WebSocketMessageData['new_message']) {
    const { conversation_id, message } = data;
    
    // Invalidate and refetch messages for this conversation
    this.queryClient.invalidateQueries({
      queryKey: messageQueryKeys.conversation(conversation_id),
    });

    // Update conversations list to reflect new last message
    this.queryClient.invalidateQueries({
      queryKey: conversationQueryKeys.lists(),
    });

    // Show notification if message is from another user
    const currentUser = useAuthStore.getState().user;
    if (message.sender_id !== currentUser?._id) {
      toast.info(`New message in conversation`);
    }
  }

  private handleMessageStatus(data: WebSocketMessageData['message_status']) {
    const { conversation_id } = data;
    
    // Invalidate messages to update status indicators
    this.queryClient.invalidateQueries({
      queryKey: messageQueryKeys.conversation(conversation_id),
    });
  }

  private handleConversationUpdate(data: WebSocketMessageData['conversation_update']) {
    const { conversation_id } = data;
    
    // Invalidate specific conversation and conversations list
    this.queryClient.invalidateQueries({
      queryKey: conversationQueryKeys.detail(conversation_id),
    });
    
    this.queryClient.invalidateQueries({
      queryKey: conversationQueryKeys.lists(),
    });
  }

  private handleNewConversation(data: WebSocketMessageData['new_conversation']) {
    const { conversation } = data;
    
    // Invalidate conversations list to show the new conversation
    this.queryClient.invalidateQueries({
      queryKey: conversationQueryKeys.lists(),
    });

    // Show notification about new conversation
    const customerName = conversation.customer?.name || 
                        conversation.customer_name || 
                        conversation.customer?.phone || 
                        conversation.customer_phone || 
                        'Unknown Customer';
                        
    toast.info(`New conversation from ${customerName}`);
    
    console.log('New conversation created:', conversation._id);
  }

  private handleUserActivity(data: WebSocketMessageData['user_activity']) {
    const { conversation_id, user_name, activity } = data;
    
    // Handle typing indicators and user presence
    // This could trigger UI updates for typing indicators
    console.log(`User ${user_name} is ${activity} in conversation ${conversation_id}`);
    
    // You can implement typing indicator state management here
    // For now, we'll just log it
  }

  /**
   * Connect with user authentication
   */
  connectWithAuth(): Promise<void> {
    const user = useAuthStore.getState().user;
    if (!user) {
      console.error('Cannot connect WebSocket: User not authenticated');
      return Promise.reject(new Error('User not authenticated'));
    }

    // Connect to WebSocket with user ID
    return this.connect(user._id);
  }

  /**
   * Clean up subscriptions on disconnect
   */
  disconnect() {
    this.subscriptions.clear();
    super.disconnect();
  }
}

// Global WebSocket client instance
let globalWebSocketClient: MessagingWebSocketClient | null = null;

export const getWebSocketClient = (queryClient: ReturnType<typeof useQueryClient>) => {
  if (!globalWebSocketClient) {
    globalWebSocketClient = new MessagingWebSocketClient(queryClient);
  }
  return globalWebSocketClient;
};