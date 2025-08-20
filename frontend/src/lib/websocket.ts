/**
 * Enhanced WebSocket client with conversation-specific messaging support.
 * Extends the base WebSocket client with real-time messaging capabilities.
 */

import { WebSocketClient } from './ws';
import { useAuthStore } from './store';
import { useQueryClient } from '@tanstack/react-query';
import { messageQueryKeys } from '@/features/messages/hooks/useMessages';
import { conversationQueryKeys } from '@/features/conversations/hooks/useConversations';
import { toast } from '@/components/feedback/Toast';

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
  
  // Messages read confirmation
  messages_read: {
    conversation_id: string;
    message_ids: string[];
    read_by_user_id: string;
    read_by_user_name: string;
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
  public queryClient: ReturnType<typeof useQueryClient>;
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
        data: data,
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
          this.handleNewMessage({
            conversation_id: data.conversation_id,
            message: data.message
          });
          break;
          
        case 'message_status':
        case 'message_status_update':
          console.log('🔔 [WEBSOCKET] Handling message status update');
          this.handleMessageStatus({
            conversation_id: data.conversation_id,
            message_id: data.message_id,
            status: data.status,
            timestamp: data.timestamp || new Date().toISOString(),
            message_data: data.message_data // Include message data for optimized updates
          });
          break;
          
        case 'conversation_update':
          console.log('🔔 [WEBSOCKET] Handling conversation update');
          this.handleConversationUpdate({
            conversation_id: data.conversation_id,
            changes: data.update || data.changes
          });
          break;
          
        case 'new_conversation':
          console.log('🔔 [WEBSOCKET] Handling new conversation');
          this.handleNewConversation({
            conversation: data.conversation
          });
          break;
          
        case 'user_activity':
          console.log('🔔 [WEBSOCKET] Handling user activity');
          this.handleUserActivity(data.data || data);
          break;
          
        case 'messages_read':
          console.log('🔔 [WEBSOCKET] Handling messages read confirmation');
          this.handleMessagesRead({
            conversation_id: data.conversation_id,
            message_ids: data.message_ids,
            read_by_user_id: data.read_by_user_id,
            read_by_user_name: data.read_by_user_name,
            timestamp: data.timestamp
          });
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
    const messageHandlers = (this as unknown as { messageHandlers?: Map<string, ((data: unknown) => void)[]> }).messageHandlers;
    if (!messageHandlers) return;

    // Notify all handlers for this message type
    const handlers = messageHandlers.get(message.type as string) || [];
    handlers.forEach((handler: (data: unknown) => void) => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in message handler:', error);
      }
    });

    // Also notify general message handlers
    const generalHandlers = messageHandlers.get('*') || [];
    generalHandlers.forEach((handler: (data: unknown) => void) => {
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
    const currentUser = useAuthStore.getState().user;
    
    console.log('🔔 [WEBSOCKET] About to update query for conversation:', conversation_id);
    
    // Check if this message should update an optimistic message
    const isFromCurrentUser = message.sender_id === currentUser?._id;
    
    if (isFromCurrentUser) {
      // Try to update optimistic message instead of adding duplicate
      const updated = this.updateOptimisticMessage(conversation_id, message);
      if (updated) {
        console.log('🔔 [WEBSOCKET] Updated optimistic message with real data');
        return; // Don't invalidate, we handled it manually
      }
    }
    
    // For messages from other users or if no optimistic message found, add to query manually
    console.log('🔔 [WHATSAPP_UX] Adding new message to infinite query smoothly...');
    
    // Update the infinite query directly for WhatsApp-style smooth experience
    this.queryClient.setQueryData(
      messageQueryKeys.conversationMessages(conversation_id, { limit: 50 }),
      (oldData: any) => {
        if (!oldData) return oldData;
        
        // Add to the first page (latest messages)
        const updatedPages = [...oldData.pages];
        if (updatedPages[0]) {
          // Check if message already exists to avoid duplicates
          const existingMessage = updatedPages[0].messages.find((m: any) => m._id === message._id);
          if (!existingMessage) {
            console.log('✅ [WHATSAPP_UX] Adding new message to query data directly');
            updatedPages[0] = {
              ...updatedPages[0],
              messages: [...updatedPages[0].messages, message]
            };
          } else {
            console.log('⚠️ [WHATSAPP_UX] Message already exists in query, skipping');
          }
        }
        
        return {
          ...oldData,
          pages: updatedPages
        };
      }
    );

    // Minimal invalidation - only mark conversation list as stale (no refetch)
    this.queryClient.invalidateQueries({
      queryKey: ['conversations'],
      refetchType: 'none'
    });

    console.log('✅ [WHATSAPP_UX] New message added smoothly, VirtualizedMessageList will handle UX');

    // Show notification if message is from another user
    if (!isFromCurrentUser) {
      console.log('🔔 [WEBSOCKET] Showing toast notification');
      toast.info(`New message in conversation`);
    }
  }

  private updateOptimisticMessage(conversationId: string, realMessage: unknown): boolean {
    let messageUpdated = false;
    
    // Update both query structures to ensure compatibility
    
    // 1. Update the messages query (for MessageList component)
    this.queryClient.setQueryData(
      messageQueryKeys.conversationMessages(conversationId, { limit: 50 }),
      (old: unknown) => {
        if (!old || typeof old !== 'object') return old;
        const oldData = old as { pages: { messages: (unknown & { isOptimistic?: boolean })[], total: number }[] };
        
        const newPages = [...oldData.pages];
        if (newPages[0]) {
          const messages = [...newPages[0].messages];
          
          // Find optimistic message that matches this real message
          const optimisticIndex = messages.findIndex((msg) => {
            const message = msg as { 
              isOptimistic?: boolean; 
              text_content?: string; 
              sender_id?: string;
              _id?: string;
              status?: string;
            };
            const real = realMessage as { 
              text_content?: string; 
              sender_id?: string;
              whatsapp_message_id?: string;
            };
            
            // More robust matching: check if message is optimistic and matches content and sender
            // Also check if it's still in "sending" or "sent" status (not yet confirmed by webhook)
            return message.isOptimistic && 
                   message.text_content === real.text_content &&
                   message.sender_id === real.sender_id &&
                   (message.status === 'sending' || message.status === 'sent');
          });
          
          if (optimisticIndex !== -1) {
            // Replace optimistic message with real message, but preserve the optimistic sender_name
            const optimisticMessage = messages[optimisticIndex] as { sender_name?: string };
            const realMessageData = realMessage as Record<string, unknown>;
            
            messages[optimisticIndex] = {
              ...realMessageData,
              _id: realMessageData['id'] || realMessageData['_id'] || '',
              status: 'sent',
              isOptimistic: false,
              // Preserve the optimistic sender_name to avoid flash
              sender_name: optimisticMessage.sender_name || realMessageData['sender_name'],
            } as unknown as typeof messages[number];
            messageUpdated = true;
            
            console.log('🔔 [WEBSOCKET] Successfully updated optimistic message with real data in messages query');
            
            newPages[0] = {
              ...newPages[0],
              messages
            };
          }
        }
        
        return {
          ...oldData,
          pages: newPages
        };
      }
    );

    // 2. Also update the conversation with messages query (for conversation page)
    this.queryClient.setQueryData(
      ['conversations', 'detail', conversationId, 'with-messages', 50, 0],
      (old: unknown) => {
        if (!old || typeof old !== 'object') return old;
        const oldData = old as { messages: (unknown & { isOptimistic?: boolean })[], messages_total: number };
        
        const messages = [...oldData.messages];
        
        // Find optimistic message that matches this real message
        const optimisticIndex = messages.findIndex((msg) => {
          const message = msg as { 
            isOptimistic?: boolean; 
            text_content?: string; 
            sender_id?: string;
            _id?: string;
            status?: string;
          };
          const real = realMessage as { 
            text_content?: string; 
            sender_id?: string;
            whatsapp_message_id?: string;
          };
          
          // More robust matching: check if message is optimistic and matches content and sender
          return message.isOptimistic && 
                 message.text_content === real.text_content &&
                 message.sender_id === real.sender_id &&
                 (message.status === 'sending' || message.status === 'sent');
        });
        
        if (optimisticIndex !== -1) {
          // Replace optimistic message with real message, but preserve the optimistic sender_name
          const optimisticMessage = messages[optimisticIndex] as { sender_name?: string };
          const realMessageData = realMessage as Record<string, unknown>;
          
          messages[optimisticIndex] = {
            ...realMessageData,
            _id: realMessageData['id'] || realMessageData['_id'] || '',
            status: 'sent',
            isOptimistic: false,
            // Preserve the optimistic sender_name to avoid flash
            sender_name: optimisticMessage.sender_name || realMessageData['sender_name'],
          } as unknown as typeof messages[number];
          messageUpdated = true;
          
          console.log('🔔 [WEBSOCKET] Successfully updated optimistic message with real data in conversation query');
        }
        
        return {
          ...oldData,
          messages
        };
      }
    );
    
    return messageUpdated;
  }

  private handleMessageStatus(data: WebSocketMessageData['message_status'] & { message_data?: any }) {
    console.log('🔔 [WEBSOCKET] Frontend received message status update:', data);
    const { conversation_id, message_id, status, message_data } = data;
    
    if (message_data) {
      // Optimized update: directly update the message in the query cache
      console.log(`🔔 [WEBSOCKET] Optimized status update: ${message_id} -> ${status}`);
      
      this.queryClient.setQueryData(
        messageQueryKeys.conversationMessages(conversation_id, { limit: 50 }),
        (oldData: any) => {
          if (!oldData) return oldData;
          
          const updatedPages = oldData.pages.map((page: any) => ({
            ...page,
            messages: page.messages.map((msg: any) => 
              msg._id === message_id 
                ? { ...msg, ...message_data, status }
                : msg
            )
          }));
          
          return {
            ...oldData,
            pages: updatedPages
          };
        }
      );
      
      console.log('🔔 [WEBSOCKET] Optimized status update applied - no query invalidation needed');
    } else {
      // Fallback: invalidate queries if no message data provided
      console.log(`🔔 [WEBSOCKET] Fallback status update: ${message_id} -> ${status}, invalidating queries...`);
      
      this.queryClient.invalidateQueries({
        queryKey: messageQueryKeys.conversationMessages(conversation_id, { limit: 50 }),
      });
    }

    // Show notification for status updates (optional)
    if (status === 'delivered' || status === 'read') {
      console.log(`🔔 [WEBSOCKET] Message ${message_id} status updated to: ${status}`);
    }
  }

  private handleConversationUpdate(data: WebSocketMessageData['conversation_update']) {
    const { conversation_id } = data;
    
    // Invalidate specific conversation and conversations list
    this.queryClient.invalidateQueries({
      queryKey: conversationQueryKeys.detail(conversation_id),
    });
    
    // Also invalidate the conversation with messages query
    this.queryClient.invalidateQueries({
      queryKey: ['conversations', 'detail', conversation_id, 'with-messages', 50, 0],
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
    const customerName = (conversation as any).customer?.name || 
                        (conversation as any).customer_name || 
                        (conversation as any).customer?.phone || 
                        (conversation as any).customer_phone || 
                        'Unknown Customer';
                        
    toast.info(`New conversation from ${customerName}`);
    
    console.log('New conversation created:', conversation._id);
  }

  private handleUserActivity(data: WebSocketMessageData['user_activity']) {
    console.log('🔔 [WEBSOCKET] Raw user activity data:', data);
    const { conversation_id, user_id, activity } = data;
    
    // Handle typing indicators and user presence
    // This could trigger UI updates for typing indicators
    console.log(`🔔 [WEBSOCKET] User ${user_id} activity: ${activity} in conversation ${conversation_id}`);
    
    // You can implement typing indicator state management here
    // For now, we'll just log it
  }

  /**
   * Handle messages read confirmation from WebSocket
   */
  private handleMessagesRead(data: {
    conversation_id: string;
    message_ids: string[];
    read_by_user_id: string;
    read_by_user_name: string;
    timestamp: string;
  }) {
    console.log('🔔 [WEBSOCKET] Handling messages read confirmation:', data);
    const { conversation_id, message_ids, read_by_user_id, read_by_user_name } = data;
    
    // Update message status to 'read' for the specified messages
    this.queryClient.setQueryData(
      messageQueryKeys.conversationMessages(conversation_id, { limit: 50 }),
      (old: unknown) => {
        if (!old || typeof old !== 'object') return old;
        const oldData = old as { pages: { messages: (unknown & { _id?: string; status?: string })[], total: number }[] };
        
        const newPages = [...oldData.pages];
        if (newPages[0]) {
          const messages = [...newPages[0].messages];
          
          // Update status for messages that were marked as read
          const updatedMessages = messages.map((msg) => {
            if (message_ids.includes(msg._id || '')) {
              return {
                ...msg,
                status: 'read'
              };
            }
            return msg;
          });
          
          newPages[0] = {
            ...newPages[0],
            messages: updatedMessages
          };
        }
        
        return {
          ...oldData,
          pages: newPages
        };
      }
    );

    // Also update the conversation with messages query
    this.queryClient.setQueryData(
      ['conversations', 'detail', conversation_id, 'with-messages', 50, 0],
      (old: unknown) => {
        if (!old || typeof old !== 'object') return old;
        const oldData = old as { messages: (unknown & { _id?: string; status?: string })[], messages_total: number };
        
        const updatedMessages = oldData.messages.map((msg) => {
          if (message_ids.includes(msg._id || '')) {
            return {
              ...msg,
              status: 'read'
            };
          }
          return msg;
        });
        
        return {
          ...oldData,
          messages: updatedMessages
        };
      }
    );

    console.log(`🔔 [WEBSOCKET] Updated ${message_ids.length} messages to 'read' status`);
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
      // Set up message handler using the parent class method
      this.setupEnhancedMessageHandler();
      
      // Subscribe to all tracked conversations after connection
      console.log('🔔 [WEBSOCKET] Re-subscribing to tracked conversations:', Array.from(this.subscriptions));
      this.subscriptions.forEach(conversationId => {
        console.log('🔔 [WEBSOCKET] Re-subscribing to conversation:', conversationId);
        this.send({
          type: 'subscribe_conversation',
          conversation_id: conversationId,
        });
      });
    }).catch((error) => {
      console.error('❌ [WEBSOCKET] Connection failed:', error);
    });
    
    return connectPromise;
  }

  /**
   * Set up enhanced message handler for the WebSocket connection
   */
  private setupEnhancedMessageHandler() {
    // Access the WebSocket instance through the parent class
    const wsInstance = (this as any).ws;
    if (wsInstance) {
      wsInstance.onmessage = (event: MessageEvent) => {
        this.handleIncomingMessage(event);
      };
    }
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
  } else {
    // Update the queryClient reference to ensure we're using the current one
    globalWebSocketClient.queryClient = queryClient;
  }
  return globalWebSocketClient;
};