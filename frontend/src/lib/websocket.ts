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
  
  // AI-generated response
  ai_response: {
    conversation_id: string;
    message: Record<string, unknown>; // AI response message object
    timestamp: string;
  };
  
  // Auto-reply toggle notification
  autoreply_toggled: {
    conversation_id: string;
    ai_autoreply_enabled: boolean;
    changed_by?: string;
    timestamp: string;
  };

  // AI processing status notifications
  ai_processing_started: {
    conversation_id: string;
    message_id: string;
    timestamp: string;
  };

  ai_agent_activity: {
    conversation_id: string;
    activity_type: string; // e.g., "rag_search", "intent_detection", "response_generation"
    activity_description: string; // e.g., "Using internal knowledge", "Analyzing message intent"
    metadata: Record<string, unknown>;
    timestamp: string;
  };

  ai_processing_completed: {
    conversation_id: string;
    message_id: string;
    success: boolean;
    response_sent: boolean;
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
   * Handle incoming WebSocket messages with enhanced logging
   */
  protected handleIncomingMessage(event: MessageEvent) {
    try {
      const data = JSON.parse(event.data);
      console.log('🔔 [WEBSOCKET] Received message:', data.type, data);
      console.log('📨 [WEBSOCKET] Frontend received message:', data);
      console.log('📨 [WEBSOCKET] Message type:', data.type);
      console.log('📨 [WEBSOCKET] Conversation ID:', data.conversation_id);
      
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
          console.log('🔔 [WEBSOCKET] Message data:', data.message);
          this.handleNewMessage({
            conversation_id: data.conversation_id,
            message: data.message
          });
          break;
          
        case 'message_status':
        case 'message_status_update':
          console.log('🔔 [WEBSOCKET] Handling message status update');
          console.log('🔔 [WEBSOCKET] Raw status update data:', data);
          console.log('🔔 [WEBSOCKET] Message ID:', data.message_id);
          console.log('🔔 [WEBSOCKET] Status:', data.status);
          console.log('🔔 [WEBSOCKET] Message data:', data.message_data);
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
          
        case 'ai_response':
          console.log('🤖 [WEBSOCKET] Handling AI response');
          console.log('🤖 [WEBSOCKET] AI message data:', data.message);
          this.handleAIResponse({
            conversation_id: data.conversation_id,
            message: data.message,
            timestamp: data.timestamp
          });
          break;
          
        case 'autoreply_toggled':
          console.log('🔔 [WEBSOCKET] Handling auto-reply toggle');
          this.handleAutoReplyToggle({
            conversation_id: data.conversation_id,
            ai_autoreply_enabled: data.ai_autoreply_enabled,
            changed_by: data.changed_by,
            timestamp: data.timestamp
          });
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

        case 'ai_processing_started':
          console.log('🤖 [WEBSOCKET] Handling AI processing started');
          this.handleAIProcessingStarted({
            conversation_id: data.conversation_id,
            message_id: data.message_id,
            timestamp: data.timestamp
          });
          break;

        case 'ai_agent_activity':
          console.log('🤖 [WEBSOCKET] Handling AI agent activity');
          this.handleAIAgentActivity({
            conversation_id: data.conversation_id,
            activity_type: data.activity_type,
            activity_description: data.activity_description,
            metadata: data.metadata || {},
            timestamp: data.timestamp
          });
          break;

        case 'ai_processing_completed':
          console.log('🤖 [WEBSOCKET] Handling AI processing completed');
          this.handleAIProcessingCompleted({
            conversation_id: data.conversation_id,
            message_id: data.message_id,
            success: data.success,
            response_sent: data.response_sent,
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
    console.log('🔔 [WEBSOCKET] handleNewMessage called with data:', data);
    const { conversation_id, message } = data;
    const currentUser = useAuthStore.getState().user;
    
    console.log('🔔 [WEBSOCKET] About to update query for conversation:', conversation_id);
    console.log('🔔 [WEBSOCKET] Current user ID:', currentUser?._id);
    console.log('🔔 [WEBSOCKET] Message sender ID:', message.sender_id);
    
    // Check if this message is from the current user (optimistic message)
    const isFromCurrentUser = message.sender_id === currentUser?._id;
    console.log('🔔 [WEBSOCKET] Is from current user:', isFromCurrentUser);
    
    // SIMPLE APPROACH: Just invalidate the query for all messages
    // This ensures we always have the latest data from the server
    
    // SIMPLE APPROACH: Just invalidate the query and let it refetch fresh data
    console.log('🔔 [WEBSOCKET] Invalidating query to refresh messages after new message');
    
    this.queryClient.invalidateQueries({
      queryKey: messageQueryKeys.conversationMessages(conversation_id, { limit: 50 }),
    });

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

  // REMOVED: Complex optimistic message handling - using simple query invalidation instead

    private handleMessageStatus(data: WebSocketMessageData['message_status'] & { message_data?: any }) {
    console.log('🔔 [WEBSOCKET] Frontend received message status update:', data);
    const { conversation_id, message_id, status, message_data } = data;
    
    console.log(`🔔 [WEBSOCKET] Processing status update: ${message_id} -> ${status}`);
    
    // SIMPLE APPROACH: Just invalidate the query and let it refetch fresh data
    console.log(`🔄 [WEBSOCKET] Invalidating query for conversation ${conversation_id} to refresh message status`);
    
    this.queryClient.invalidateQueries({
      queryKey: messageQueryKeys.conversationMessages(conversation_id, { limit: 50 }),
    });
    
    console.log(`✅ [WEBSOCKET] Query invalidated successfully for status update: ${message_id} -> ${status}`);
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
   * Test WebSocket connection and message handling
   */
  testConnection() {
    console.log('🧪 [WEBSOCKET] Testing WebSocket connection...');
    console.log('🧪 [WEBSOCKET] Active connections:', (this as any).active_connections);
    console.log('🧪 [WEBSOCKET] Subscriptions:', this.subscriptions);
    
    // Test if we can send a message
    this.send({
      type: 'ping',
      data: { test: true, timestamp: Date.now() }
    });
    
    // Test custom event dispatching
    console.log('🧪 [WEBSOCKET] Testing custom event dispatching...');
    const testEvent = new CustomEvent('ai-processing-started', {
      detail: {
        conversationId: 'test-conversation',
        timestamp: new Date().toISOString()
      }
    });
    window.dispatchEvent(testEvent);
    console.log('🧪 [WEBSOCKET] Test event dispatched');
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
   * Handle AI-generated response message
   */
  private handleAIResponse(data: WebSocketMessageData['ai_response']) {
    console.log('🤖 [WEBSOCKET] handleAIResponse called with data:', data);
    
    // Treat AI responses the same as new messages for UI updates
    this.handleNewMessage({
      conversation_id: data.conversation_id,
      message: data.message
    });

    // Show specific toast for AI response
    toast.info('🤖 AI Assistant responded');
  }

  /**
   * Handle auto-reply toggle notification
   */
  private handleAutoReplyToggle(data: WebSocketMessageData['autoreply_toggled']) {
    console.log('🔔 [WEBSOCKET] handleAutoReplyToggle called with data:', data);
    
    const { conversation_id, ai_autoreply_enabled, changed_by } = data;

    // Invalidate conversation queries to refresh the toggle state
    this.queryClient.invalidateQueries({
      queryKey: ['conversation', conversation_id],
    });

    // Show notification about the change
    const action = ai_autoreply_enabled ? 'enabled' : 'disabled';
    const actor = changed_by || 'An agent';
    
    toast.info(`AI Auto-reply ${action}: ${actor} ${action} AI automatic responses`);
  }

  /**
   * Handle AI processing started notification
   */
  private handleAIProcessingStarted(data: WebSocketMessageData['ai_processing_started']) {
    console.log('🤖 [WEBSOCKET] handleAIProcessingStarted called with data:', data);
    console.log('🤖 [WEBSOCKET] Dispatching ai-processing-started event for conversation:', data.conversation_id);
    
    const { conversation_id } = data;

    // Trigger AI typing indicator by dispatching a custom event
    const event = new CustomEvent('ai-processing-started', {
      detail: {
        conversationId: conversation_id,
        timestamp: data.timestamp
      }
    });
    window.dispatchEvent(event);
    console.log('🤖 [WEBSOCKET] ai-processing-started event dispatched');
  }

  /**
   * Handle AI agent activity notification
   */
  private handleAIAgentActivity(data: WebSocketMessageData['ai_agent_activity']) {
    console.log('🤖 [WEBSOCKET] handleAIAgentActivity called with data:', data);
    console.log('🤖 [WEBSOCKET] Dispatching ai-agent-activity event for conversation:', data.conversation_id);
    
    const { conversation_id, activity_type, activity_description } = data;

    // Trigger AI activity update by dispatching a custom event
    const event = new CustomEvent('ai-agent-activity', {
      detail: {
        conversationId: conversation_id,
        activityType: activity_type,
        activityDescription: activity_description,
        timestamp: data.timestamp
      }
    });
    window.dispatchEvent(event);
    console.log('🤖 [WEBSOCKET] ai-agent-activity event dispatched');
  }

  /**
   * Handle AI processing completed notification
   */
  private handleAIProcessingCompleted(data: WebSocketMessageData['ai_processing_completed']) {
    console.log('🤖 [WEBSOCKET] handleAIProcessingCompleted called with data:', data);
    console.log('🤖 [WEBSOCKET] Dispatching ai-processing-completed event for conversation:', data.conversation_id);
    
    const { conversation_id, success, response_sent } = data;

    // Trigger AI processing completed by dispatching a custom event
    const event = new CustomEvent('ai-processing-completed', {
      detail: {
        conversationId: conversation_id,
        success,
        responseSent: response_sent,
        timestamp: data.timestamp
      }
    });
    window.dispatchEvent(event);
    console.log('🤖 [WEBSOCKET] ai-processing-completed event dispatched');
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

// Add global test function for debugging
if (typeof window !== 'undefined') {
  (window as any).testWebSocket = () => {
    if (globalWebSocketClient) {
      globalWebSocketClient.testConnection();
    } else {
      console.log('❌ [WEBSOCKET] No global WebSocket client available');
    }
  };
  
  (window as any).testAITyping = () => {
    console.log('🧪 [TEST] Testing AI typing indicator...');
    const testEvent = new CustomEvent('ai-processing-started', {
      detail: {
        conversationId: 'test-conversation',
        timestamp: new Date().toISOString()
      }
    });
    window.dispatchEvent(testEvent);
    console.log('🧪 [TEST] AI processing started event dispatched');
    
    setTimeout(() => {
      const activityEvent = new CustomEvent('ai-agent-activity', {
        detail: {
          conversationId: 'test-conversation',
          activityType: 'rag_search',
          activityDescription: 'Using internal knowledge',
          timestamp: new Date().toISOString()
        }
      });
      window.dispatchEvent(activityEvent);
      console.log('🧪 [TEST] AI agent activity event dispatched');
    }, 1000);
    
    setTimeout(() => {
      const completedEvent = new CustomEvent('ai-processing-completed', {
        detail: {
          conversationId: 'test-conversation',
          success: true,
          responseSent: true,
          timestamp: new Date().toISOString()
        }
      });
      window.dispatchEvent(completedEvent);
      console.log('🧪 [TEST] AI processing completed event dispatched');
    }, 3000);
  };
}