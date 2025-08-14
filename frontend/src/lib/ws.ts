/**
 * WebSocket client for real-time messaging updates.
 * Handles connection management, reconnection logic, and message routing.
 */

import { getWsUrl } from './config';

export interface WebSocketMessage {
  type: 'new_message' | 'message_status' | 'conversation_update' | 'user_activity' | 'typing_start' | 'typing_stop' | 'messages_read' | 'unread_count_update' | 'messages_read_confirmed';
  data: unknown;
  timestamp: string;
  user_id?: string;
  conversation_id?: string;
}

export type MessageHandler = (message: WebSocketMessage) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private url: string = '';
  private messageHandlers: Map<string, MessageHandler[]> = new Map();
  private isConnecting = false;
  private isIntentionallyClosed = false;

  /**
   * Connect to WebSocket server for a specific user
   */
  connect(userId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      // If already connected to the same user, resolve immediately
      if (this.ws?.readyState === WebSocket.OPEN && this.url.includes(userId)) {
        resolve();
        return;
      }

      // If connecting to the same user, wait for current connection
      if (this.isConnecting && this.url.includes(userId)) {
        // Return a promise that will resolve when connection completes
        const checkConnection = () => {
          if (!this.isConnecting) {
            if (this.ws?.readyState === WebSocket.OPEN) {
              resolve();
            } else {
              reject(new Error('Connection failed'));
            }
          } else {
            setTimeout(checkConnection, 100);
          }
        };
        checkConnection();
        return;
      }

      // Close existing connection if connecting to different user
      if (this.ws && this.ws.readyState !== WebSocket.CLOSED) {
        this.isIntentionallyClosed = true;
        this.ws.close();
      }

      this.isConnecting = true;
      this.isIntentionallyClosed = false;
      const wsUrl = getWsUrl();
      this.url = `${wsUrl}/chat/${userId}`;

      try {
        this.ws = new WebSocket(this.url);
        
        this.ws.onopen = () => {
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          console.log('WebSocket connected');
          resolve();
        };

        this.ws.onclose = (event: CloseEvent) => {
          this.isConnecting = false;
          console.log('WebSocket disconnected', event.code, event.reason);
          
          if (!event.wasClean && !this.isIntentionallyClosed && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect(userId);
          }
        };

        this.ws.onerror = (error: Event) => {
          this.isConnecting = false;
          console.error('WebSocket error:', error);
          console.error('WebSocket URL:', this.url);
          
          // Don't reject immediately, let the onclose handler handle reconnection
          if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            reject(new Error(`WebSocket connection failed to ${this.url}`));
          }
        };

        this.ws.onmessage = (event: MessageEvent) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  private scheduleReconnect(userId: string): void {
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    
    setTimeout(() => {
      if (!this.isIntentionallyClosed) {
        this.reconnectAttempts++;
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.connect(userId).catch(() => {
          // Reconnection failed, will try again if attempts remaining
        });
      }
    }, delay);
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(message: WebSocketMessage): void {
    // Notify all handlers for this message type
    const handlers = this.messageHandlers.get(message.type) || [];
    handlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in message handler:', error);
      }
    });

    // Also notify general message handlers
    const generalHandlers = this.messageHandlers.get('*') || [];
    generalHandlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in general message handler:', error);
      }
    });
  }

  /**
   * Subscribe to specific message types
   */
  subscribe(messageType: string, handler: MessageHandler): () => void {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, []);
    }
    
    this.messageHandlers.get(messageType)!.push(handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.messageHandlers.get(messageType);
      if (handlers) {
        const index = handlers.indexOf(handler);
        if (index > -1) {
          handlers.splice(index, 1);
        }
      }
    };
  }

  /**
   * Send a message to the server
   */
  send(data: unknown): void {
    console.log('📤 [WS] Attempting to send message:', data);
    console.log('📤 [WS] WebSocket state:', this.ws?.readyState);
    
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
      console.log('✅ [WS] Message sent successfully');
    } else {
      console.warn('❌ [WS] WebSocket is not connected. Cannot send message.');
    }
  }

  /**
   * Send typing start indicator
   */
  sendTypingStart(conversationId: string): void {
    this.send({
      type: 'typing_start',
      conversation_id: conversationId,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Send typing stop indicator
   */
  sendTypingStop(conversationId: string): void {
    this.send({
      type: 'typing_stop',
      conversation_id: conversationId,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Subscribe to a conversation for real-time updates
   */
  subscribeToConversation(conversationId: string): void {
    this.send({
      type: 'subscribe_conversation',
      conversation_id: conversationId,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Unsubscribe from a conversation
   */
  unsubscribeFromConversation(conversationId: string): void {
    this.send({
      type: 'unsubscribe_conversation',
      conversation_id: conversationId,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Mark messages as read via WebSocket
   */
  markMessagesAsRead(conversationId: string): void {
    console.log('📤 [WS] Sending mark_messages_read for conversation:', conversationId);
    console.log('📤 [WS] WebSocket connected:', this.isConnected);
    
    this.send({
      type: 'mark_messages_read',
      conversation_id: conversationId,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Mark conversation as read
   */
  markConversationAsRead(conversationId: string): void {
    this.send({
      type: 'mark_conversation_read',
      conversation_id: conversationId,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Disconnect WebSocket connection
   */
  disconnect(): void {
    this.isIntentionallyClosed = true;
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnecting');
      this.ws = null;
    }
    
    // Clear all message handlers
    this.messageHandlers.clear();
  }

  /**
   * Get current connection state
   */
  get connectionState(): string {
    if (!this.ws) return 'DISCONNECTED';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'CONNECTING';
      case WebSocket.OPEN:
        return 'CONNECTED';
      case WebSocket.CLOSING:
        return 'CLOSING';
      case WebSocket.CLOSED:
        return 'DISCONNECTED';
      default:
        return 'UNKNOWN';
    }
  }

  /**
   * Check if WebSocket is connected
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Get WebSocket instance for debugging
   */
  get wsInstance(): WebSocket | null {
    return this.ws;
  }
}

// Export singleton instance
export const wsClient = new WebSocketClient();