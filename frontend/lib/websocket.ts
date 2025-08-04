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
      console.log('🔔 [WEBSOCKET] Already subscribed to conversation:', conversationId);
      return; // Already subscribed
    }

    console.log('🔔 [WEBSOCKET] Subscribing to conversation:', conversationId);
    this.subscriptions.add(conversationId);
    
    // Send subscription request if connected, or queue it for when connected
    const subscriptionMessage = {
      type: 'subscribe_conversation',
      conversation_id: conversationId,
    };
    
    if (this.isConnected) {
      console.log('🔔 [WEBSOCKET] Sending subscription immediately');
      this.send(subscriptionMessage);
    } else {
      console.log('🔔 [WEBSOCKET] WebSocket not connected, will subscribe after connection');
      // The connection will trigger re-subscription in connectWithAuth
    }
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
      console.log('📨 [WEBSOCKET] Frontend received message:', data);
      
      // Create a WebSocket message in the format expected by the parent class
      const webSocketMessage = {
        type: data.type,
        data: data.data || data,
        timestamp: data.timestamp || new Date().toISOString(),
        conversation_id: data.conversation_id,
        user_id: data.user_id
      };
      
      // Trigger the parent class message handlers by calling the subscription handlers directly
      this.triggerMessageHandlers(webSocketMessage);
      
      // Then handle specific message types for UI updates
      switch (data.type) {
        case 'new_message':
          console.log('🔔 [WEBSOCKET] Handling new_message');
          this.handleNewMessage(data.data || data);
          break;
          
        case 'message_status':
        case 'message_status_update':
          console.log('🔔 [WEBSOCKET] Handling message status update');
          this.handleMessageStatus(data.data || data);
          break;
          
        case 'conversation_update':
          console.log('🔔 [WEBSOCKET] Handling conversation update');
          this.handleConversationUpdate(data.data || data);
          break;
          
        case 'new_conversation':
          console.log('🔔 [WEBSOCKET] Handling new conversation');
          this.handleNewConversation(data.data || data);
          break;
          
        case 'user_activity':
          console.log('🔔 [WEBSOCKET] Handling user activity');
          this.handleUserActivity(data.data || data);
          break;
          
        case 'subscription_confirmed':
          console.log('✅ [WEBSOCKET] Subscription confirmed for conversation:', data.conversation_id);
          this.updateSubscriptionStatus(data.conversation_id, true);
          break;
          
        case 'subscription_already_active':
          console.log('📋 [WEBSOCKET] Subscription already active for conversation:', data.conversation_id);
          this.updateSubscriptionStatus(data.conversation_id, true);
          break;
          
        case 'unsubscription_confirmed':
          console.log('✅ [WEBSOCKET] Unsubscription confirmed for conversation:', data.conversation_id);
          this.updateSubscriptionStatus(data.conversation_id, false);
          break;
          
        default:
          console.log('❓ [WEBSOCKET] Unknown message type:', data.type, data);
      }
    } catch (error) {
      console.error('❌ [WEBSOCKET] Error handling message:', error);
    }
  }

  /**
   * Update subscription status callback for hooks
   */
  private subscriptionStatusCallbacks: Map<string, (isSubscribed: boolean) => void> = new Map();

  /**
   * Register a callback for subscription status updates
   */
  public onSubscriptionStatusChange(conversationId: string, callback: (isSubscribed: boolean) => void) {
    this.subscriptionStatusCallbacks.set(conversationId, callback);
  }

  /**
   * Remove subscription status callback
   */
  public offSubscriptionStatusChange(conversationId: string) {
    this.subscriptionStatusCallbacks.delete(conversationId);
  }

  /**
   * Update subscription status from server confirmations
   */
  private updateSubscriptionStatus(conversationId: string, isSubscribed: boolean) {
    const callback = this.subscriptionStatusCallbacks.get(conversationId);
    if (callback) {
      callback(isSubscribed);
    }
  }

  /**
   * Manually trigger message handlers for backward compatibility
   */
  private triggerMessageHandlers(message: Record<string, unknown>) {
    // Access the protected messageHandlers map from the parent class
    const messageHandlers = (this as unknown as { messageHandlers?: Map<string, Function[]> }).messageHandlers;
    if (!messageHandlers) return;

    // Notify all handlers for this message type
    const handlers = messageHandlers.get(message.type as string) || [];
    handlers.forEach((handler: Function) => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in message handler:', error);
      }
    });

    // Also notify general message handlers
    const generalHandlers = messageHandlers.get('*') || [];
    generalHandlers.forEach((handler: Function) => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in general message handler:', error);
      }
    });
  }

  private handleNewMessage(data: WebSocketMessageData['new_message']) {
    console.log('🔔 [WEBSOCKET] Frontend received new message:', data);
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
    console.log('🔔 [WEBSOCKET] Current user:', currentUser?._id, 'Message sender:', message.sender_id);
    if (message.sender_id !== currentUser?._id) {
      console.log('🔔 [WEBSOCKET] Showing toast notification');
      toast.info(`New message in conversation`);
    } else {
      console.log('🔔 [WEBSOCKET] Not showing notification - message from current user');
    }
  }

  private handleMessageStatus(data: WebSocketMessageData['message_status']) {
    console.log('🔔 [WEBSOCKET] Frontend received message status update:', data);
    const { conversation_id, message_id, status } = data;
    
    // Invalidate messages to update status indicators
    this.queryClient.invalidateQueries({
      queryKey: messageQueryKeys.conversation(conversation_id),
    });
    
    // Show notification for status updates (optional)
    if (status === 'delivered' || status === 'read') {
      console.log(`🔔 [WEBSOCKET] Message ${message_id} status: ${status}`);
    }
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
    console.log('🔔 [WEBSOCKET] Raw user activity data:', data);
    const { conversation_id, user_id, activity } = data;
    
    // Handle typing indicators and user presence
    // This could trigger UI updates for typing indicators
    console.log(`🔔 [WEBSOCKET] User ${user_id} activity: ${activity?.type} in conversation ${conversation_id}`);
    
    // You can implement typing indicator state management here
    // For now, we'll just log it
  }

  /**
   * Connect with user authentication and set up message handling
   */
  connectWithAuth(): Promise<void> {
    const user = useAuthStore.getState().user;
    if (!user) {
      console.error('❌ [WEBSOCKET] Cannot connect: User not authenticated');
      return Promise.reject(new Error('User not authenticated'));
    }

    console.log('🔌 [WEBSOCKET] Connecting with user ID:', user._id);
    
    // Connect to WebSocket with user ID
    const connectPromise = this.connect(user._id);
    
    // Override the onmessage handler after connection to use our enhanced handling
    connectPromise.then(() => {
      console.log('✅ [WEBSOCKET] Connection established, setting up message handler');
      if (this.ws) {
        this.ws.onmessage = (event: MessageEvent) => {
          this.handleIncomingMessage(event);
        };
        
        // Subscribe to all tracked conversations after connection
        console.log('🔔 [WEBSOCKET] Re-subscribing to tracked conversations:', Array.from(this.subscriptions));
        this.subscriptions.forEach(conversationId => {
          console.log('🔔 [WEBSOCKET] Re-subscribing to conversation:', conversationId);
          this.send({
            type: 'subscribe_conversation',
            conversation_id: conversationId,
          });
        });
      }
    }).catch((error) => {
      console.error('❌ [WEBSOCKET] Connection failed:', error);
    });
    
    return connectPromise;
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