/**
 * Dashboard WebSocket client for real-time dashboard updates.
 * Handles conversation list, stats, and unread count updates.
 */

import { WebSocketClient } from './ws';
import { useAuthStore } from './store';
import { getWsUrl } from './config';
import { useQueryClient } from '@tanstack/react-query';
import { conversationQueryKeys } from '@/features/conversations/hooks/useConversations';
import { toast } from '@/components/ui/Toast';

// Dashboard WebSocket message types
export interface DashboardWebSocketMessageData {
  // New conversation created
  new_conversation: {
    conversation: Record<string, unknown>;
    timestamp: string;
  };
  
  // Conversation list update (created, updated, status_changed)
  conversation_list_update: {
    update_type: 'created' | 'updated' | 'status_changed';
    conversation: Record<string, unknown>;
    timestamp: string;
  };
  
  // Dashboard stats update
  stats_update: {
    stats: Record<string, unknown>;
    timestamp: string;
  };
  
  // Unread count update for specific conversation
  unread_count_update: {
    conversation_id: string;
    unread_count: number;
    timestamp: string;
  };
  
  // Initial unread counts when connecting
  initial_unread_counts: {
    unread_counts: Record<string, number>;
    timestamp: string;
  };
}

export type DashboardMessageHandler = (data: DashboardWebSocketMessageData[keyof DashboardWebSocketMessageData]) => void;

export class DashboardWebSocketClient extends WebSocketClient {
  public queryClient: ReturnType<typeof useQueryClient>;
  private isDashboardSubscribed = false;
  private unreadCounts = new Map<string, number>();
  private messageHandlers = new Map<string, DashboardMessageHandler[]>();
  
  // Properties from base class that we need for dashboard WebSocket
  protected isConnecting = false;
  protected isIntentionallyClosed = false;
  protected reconnectAttempts = 0;
  protected maxReconnectAttempts = 5;
  protected reconnectDelay = 1000;

  constructor(queryClient: ReturnType<typeof useQueryClient>) {
    super();
    this.queryClient = queryClient;
  }

  /**
   * Subscribe to dashboard updates
   */
  subscribeToDashboard() {
    if (this.isDashboardSubscribed) {
      console.log('🏠 [DASHBOARD_WS] Already subscribed to dashboard');
      return;
    }

    console.log('🏠 [DASHBOARD_WS] Subscribing to dashboard updates');
    this.isDashboardSubscribed = true;
    
    if (this.isConnected) {
      console.log('🏠 [DASHBOARD_WS] Sending dashboard subscription immediately');
      this.send({ type: 'subscribe_dashboard' });
    } else {
      console.log('🏠 [DASHBOARD_WS] WebSocket not connected, will subscribe after connection');
    }
  }

  /**
   * Unsubscribe from dashboard updates
   */
  unsubscribeFromDashboard() {
    if (!this.isDashboardSubscribed) {
      return;
    }

    this.isDashboardSubscribed = false;
    this.send({ type: 'unsubscribe_dashboard' });
    console.log('🏠 [DASHBOARD_WS] Unsubscribed from dashboard updates');
  }

  /**
   * Mark a conversation as read (reset unread count)
   */
  markConversationAsRead(conversationId: string) {
    this.unreadCounts.set(conversationId, 0);
    this.send({
      type: 'mark_conversation_read',
      conversation_id: conversationId,
    });
    console.log('📖 [DASHBOARD_WS] Marked conversation as read:', conversationId);
  }

  /**
   * Get unread count for a conversation
   */
  getUnreadCount(conversationId: string): number {
    return this.unreadCounts.get(conversationId) || 0;
  }

  /**
   * Get all unread counts
   */
  getAllUnreadCounts(): Record<string, number> {
    return Object.fromEntries(this.unreadCounts);
  }

  /**
   * Add message handler for specific message type
   */
  addMessageHandler<T extends keyof DashboardWebSocketMessageData>(
    messageType: T, 
    handler: (data: DashboardWebSocketMessageData[T]) => void
  ) {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, []);
    }
    this.messageHandlers.get(messageType)!.push(handler as DashboardMessageHandler);
  }

  /**
   * Remove message handler
   */
  removeMessageHandler<T extends keyof DashboardWebSocketMessageData>(
    messageType: T, 
    handler: (data: DashboardWebSocketMessageData[T]) => void
  ) {
    const handlers = this.messageHandlers.get(messageType);
    if (handlers) {
      const index = handlers.indexOf(handler as DashboardMessageHandler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * Handle incoming WebSocket messages
   */
  protected override handleIncomingMessage(event: MessageEvent) {
    try {
      const data = JSON.parse(event.data);
      console.log('📨 [DASHBOARD_WS] Received message:', data);

      switch (data.type) {
        case 'new_conversation':
          this.handleNewConversation(data);
          break;
        
        case 'conversation_list_update':
          this.handleConversationListUpdate(data);
          break;
        
        case 'stats_update':
          this.handleStatsUpdate(data);
          break;
        
        case 'unread_count_update':
          this.handleUnreadCountUpdate(data);
          break;
        
        case 'initial_unread_counts':
          this.handleInitialUnreadCounts(data);
          break;
        
        case 'dashboard_subscription_confirmed':
          console.log('✅ [DASHBOARD_WS] Dashboard subscription confirmed');
          break;
        
        case 'error':
          console.error('❌ [DASHBOARD_WS] Error from server:', data.message);
          toast({
            title: 'Connection Error',
            description: 'Real-time updates may be delayed. Please refresh if issues persist.',
            variant: 'destructive',
          });
          break;
        
        default:
          console.log('🤷 [DASHBOARD_WS] Unknown message type:', data.type);
      }
    } catch (error) {
      console.error('❌ [DASHBOARD_WS] Error parsing WebSocket message:', error);
    }
  }

  private handleNewConversation(data: any) {
    console.log('🆕 [DASHBOARD_WS] New conversation:', data.conversation);
    
    // Invalidate conversation queries to refresh the list
    this.queryClient.invalidateQueries({
      queryKey: conversationQueryKeys.lists(),
    });
    
    // Invalidate stats to update counters
    this.queryClient.invalidateQueries({
      queryKey: conversationQueryKeys.stats(),
    });
    
    // Call custom handlers
    const handlers = this.messageHandlers.get('new_conversation');
    if (handlers) {
      handlers.forEach(handler => handler(data));
    }
    
    // Show toast notification
    toast({
      title: 'New Conversation',
      description: `New conversation started with ${data.conversation.customer_name || data.conversation.customer_phone}`,
    });
  }

  private handleConversationListUpdate(data: any) {
    console.log('🔄 [DASHBOARD_WS] Conversation list update:', data.update_type, data.conversation);
    
    // Invalidate conversation queries to refresh the list
    this.queryClient.invalidateQueries({
      queryKey: conversationQueryKeys.lists(),
    });
    
    // If it's a status change, also update stats
    if (data.update_type === 'status_changed') {
      this.queryClient.invalidateQueries({
        queryKey: conversationQueryKeys.stats(),
      });
    }
    
    // Call custom handlers
    const handlers = this.messageHandlers.get('conversation_list_update');
    if (handlers) {
      handlers.forEach(handler => handler(data));
    }
  }

  private handleStatsUpdate(data: any) {
    console.log('📊 [DASHBOARD_WS] Stats update:', data.stats);
    
    // Update the stats query cache directly with new data
    this.queryClient.setQueryData(conversationQueryKeys.stats(), data.stats);
    
    // Call custom handlers
    const handlers = this.messageHandlers.get('stats_update');
    if (handlers) {
      handlers.forEach(handler => handler(data));
    }
  }

  private handleUnreadCountUpdate(data: any) {
    console.log('📊 [DASHBOARD_WS] Unread count update:', data.conversation_id, data.unread_count);
    
    // Update local unread count
    this.unreadCounts.set(data.conversation_id, data.unread_count);
    
    // Call custom handlers
    const handlers = this.messageHandlers.get('unread_count_update');
    if (handlers) {
      handlers.forEach(handler => handler(data));
    }
  }

  private handleInitialUnreadCounts(data: any) {
    console.log('📊 [DASHBOARD_WS] Initial unread counts:', data.unread_counts);
    
    // Load initial unread counts
    Object.entries(data.unread_counts).forEach(([conversationId, count]) => {
      this.unreadCounts.set(conversationId, count as number);
    });
    
    // Call custom handlers
    const handlers = this.messageHandlers.get('initial_unread_counts');
    if (handlers) {
      handlers.forEach(handler => handler(data));
    }
  }

  /**
   * Connect with user authentication and set up dashboard subscription
   */
  connectWithAuth(): Promise<void> {
    const user = useAuthStore.getState().user;
    if (!user) {
      console.error('❌ [DASHBOARD_WS] Cannot connect: User not authenticated');
      return Promise.reject(new Error('User not authenticated'));
    }

    console.log('🔌 [DASHBOARD_WS] Connecting with user ID:', user._id);
    
    // Connect to dashboard WebSocket with user ID
    const connectPromise = this.connectToDashboard(user._id);
    
    // Set up message handling and auto-subscribe after connection
    connectPromise.then(() => {
      console.log('✅ [DASHBOARD_WS] Connection established, setting up message handler');
      if (this.ws) {
        this.ws.onmessage = (event: MessageEvent) => {
          this.handleIncomingMessage(event);
        };
        
        // Auto-subscribe to dashboard updates
        if (this.isDashboardSubscribed) {
          console.log('🔔 [DASHBOARD_WS] Re-subscribing to dashboard');
          this.send({ type: 'subscribe_dashboard' });
        }
      }
    }).catch((error) => {
      console.error('❌ [DASHBOARD_WS] Connection failed:', error);
    });
    
    return connectPromise;
  }

  /**
   * Connect to dashboard WebSocket endpoint
   */
  connectToDashboard(userId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      // Determine WebSocket base URL using shared config helper
      const wsUrl = getWsUrl();

      // If already connected to the same user, resolve immediately
      if (this.ws?.readyState === WebSocket.OPEN && this.url.includes(userId)) {
        resolve();
        return;
      }

      // Close existing connection if connecting to different user
      if (this.ws && this.ws.readyState !== WebSocket.CLOSED) {
        this.isIntentionallyClosed = true;
        this.ws.close();
      }

      this.isConnecting = true;
      this.isIntentionallyClosed = false;
      this.url = `${wsUrl}/dashboard/${userId}`;

      console.log('🏠 [DASHBOARD_WS] Debug URL construction:');
      console.log('  - wsUrl:', wsUrl);
      console.log('  - userId:', userId);
      console.log('  - final URL:', this.url);

      try {
        this.ws = new WebSocket(this.url);
        
        this.ws.onopen = () => {
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          console.log('🏠 [DASHBOARD_WS] WebSocket connected');
          resolve();
        };

        this.ws.onclose = (event: CloseEvent) => {
          this.isConnecting = false;
          console.log('🏠 [DASHBOARD_WS] WebSocket disconnected', event.code, event.reason);
          
          if (!this.isIntentionallyClosed && this.reconnectAttempts < this.maxReconnectAttempts) {
            setTimeout(() => {
              this.reconnectAttempts++;
              console.log(`🔄 [DASHBOARD_WS] Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
              this.connectToDashboard(userId);
            }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts));
          }
        };

        this.ws.onerror = (error: Event) => {
          this.isConnecting = false;
          console.error('🏠 [DASHBOARD_WS] WebSocket error:', error);
          reject(new Error('WebSocket connection failed'));
        };

      } catch (error) {
        this.isConnecting = false;
        console.error('🏠 [DASHBOARD_WS] Failed to create WebSocket:', error);
        reject(error);
      }
    });
  }

  /**
   * Clean up subscriptions on disconnect
   */
  disconnect() {
    this.isDashboardSubscribed = false;
    this.unreadCounts.clear();
    this.messageHandlers.clear();
    super.disconnect();
  }
}

// Create a singleton instance
let dashboardWebSocketInstance: DashboardWebSocketClient | null = null;

export function createDashboardWebSocketClient(queryClient: ReturnType<typeof useQueryClient>): DashboardWebSocketClient {
  if (!dashboardWebSocketInstance) {
    dashboardWebSocketInstance = new DashboardWebSocketClient(queryClient);
  }
  return dashboardWebSocketInstance;
}

export function getDashboardWebSocketClient(): DashboardWebSocketClient | null {
  return dashboardWebSocketInstance;
}