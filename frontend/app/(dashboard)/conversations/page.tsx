/**
 * Conversations page - main dashboard page for managing WhatsApp conversations.
 */

'use client';

import { useState, useMemo, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Pagination } from '@/components/ui/Pagination';
import { useAuthStore } from '@/lib/store';
import { getUserDisplayName } from '@/lib/auth';
import { useConversations, useConversationStats } from '@/features/conversations/hooks/useConversations';
import { ConversationFilters, Conversation } from '@/features/conversations/models/conversation';
import { ConversationFilters as ConversationFiltersComponent } from '@/features/conversations/components/ConversationFilters';
import { ConversationListItem } from '@/features/conversations/components/ConversationListItem';
import { useUsers } from '@/features/users/hooks/useUsers';
import { useNotifications } from '@/components/feedback/NotificationSystem';
import { useDashboardWebSocket } from '@/hooks/useDashboardWebSocket';
import { NewConversationModal } from '@/components/conversations/NewConversationModal';
import { 
  PlusIcon, 
  MagnifyingGlassIcon,
  ChatBubbleLeftRightIcon,
  ClockIcon,
  UserIcon,
} from '@heroicons/react/24/outline';

export default function ConversationsPage() {
  const { user } = useAuthStore();
  const { showError } = useNotifications();
  const [filters, setFilters] = useState<ConversationFilters>({
    page: 1,
    per_page: 20,
    sort_by: 'updated_at',
    sort_order: 'desc',
  });
  const [isNewConversationModalOpen, setIsNewConversationModalOpen] = useState(false);

  const { data: conversationsData, isLoading, error } = useConversations(filters);
  const { data: stats, isLoading: statsLoading } = useConversationStats();
  
  // Dashboard WebSocket for real-time updates
  const { 
    isConnected: wsConnected, 
    unreadCounts, 
    getUnreadCount,
    getTotalUnreadCount,
    markConversationAsRead 
  } = useDashboardWebSocket();

  // Extract unique assigned agent IDs from conversations
  const assignedAgentIds = useMemo(() => {
    if (!conversationsData?.conversations) return [];
    
    const uniqueIds = new Set<string>();
    conversationsData.conversations.forEach((conversation: Conversation) => {
      if (conversation.assigned_agent_id) {
        uniqueIds.add(conversation.assigned_agent_id);
      }
    });
    
    return Array.from(uniqueIds);
  }, [conversationsData?.conversations]);

  // Fetch all assigned agents in bulk
  const { data: assignedAgents = [], isLoading: agentsLoading, error: agentsError } = useUsers(assignedAgentIds);

  // Create a map for quick agent lookup
  const agentsMap = useMemo(() => {
    const map = new Map();
    assignedAgents.forEach(agent => {
      map.set(agent._id, agent);
    });
    return map;
  }, [assignedAgents]);

  // Merge conversations with real-time unread counts
  const conversationsWithUnreadCounts = useMemo(() => {
    if (!conversationsData?.conversations) return [];
    
    return conversationsData.conversations.map((conversation: Conversation) => ({
      ...conversation,
      unread_count: getUnreadCount(conversation._id)
    }));
  }, [conversationsData?.conversations, getUnreadCount]);

  // Show error notification if agent data fails to load
  useEffect(() => {
    if (agentsError && assignedAgentIds.length > 0) {
      showError('Failed to load agent information for conversations. Some agent names may not display correctly.', 'agents-load-error');
    }
  }, [agentsError, assignedAgentIds.length, showError]);

  const handleFiltersChange = (newFilters: ConversationFilters) => {
    setFilters(newFilters);
  };

  const handleClearFilters = () => {
    setFilters({
      page: 1,
      per_page: 20,
      sort_by: 'updated_at',
      sort_order: 'desc',
    });
  };

  const handleConversationClick = (conversation: Conversation) => {
    // Mark conversation as read when clicked
    if (getUnreadCount(conversation._id) > 0) {
      markConversationAsRead(conversation._id);
    }
    // Navigate to conversation
    window.location.href = `/conversations/${conversation._id}`;
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-bold text-foreground">Conversations</h1>
            
            {/* WebSocket connection status */}
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-xs text-muted-foreground">
                {wsConnected ? 'Live' : 'Offline'}
              </span>
            </div>
            
            {/* Total unread count */}
            {getTotalUnreadCount() > 0 && (
              <Badge variant="destructive" className="text-xs">
                {getTotalUnreadCount()} unread
              </Badge>
            )}
          </div>
          <p className="text-muted-foreground">
            Welcome back, {user ? getUserDisplayName(user) : 'User'}!
          </p>
        </div>
        <Button onClick={() => setIsNewConversationModalOpen(true)}>
          <PlusIcon className="w-4 h-4 mr-2" />
          New Conversation
        </Button>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Active</p>
                <p className="text-2xl font-bold">
                  {statsLoading ? '...' : stats?.active_conversations || 0}
                </p>
              </div>
              <ChatBubbleLeftRightIcon className="w-8 h-8 text-primary-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Pending</p>
                <p className="text-2xl font-bold">
                  {statsLoading ? '...' : (stats?.total_conversations || 0) - (stats?.active_conversations || 0) - (stats?.closed_conversations || 0)}
                </p>
              </div>
              <ClockIcon className="w-8 h-8 text-warning" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Closed</p>
                <p className="text-2xl font-bold">
                  {statsLoading ? '...' : stats?.closed_conversations || 0}
                </p>
              </div>
              <Badge variant="secondary">Today</Badge>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Avg Response</p>
                <p className="text-2xl font-bold">
                  {statsLoading ? '...' : `${Math.round(stats?.average_response_time_minutes || 0)}m`}
                </p>
              </div>
              <Badge variant="success">↓ 30s</Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <ConversationFiltersComponent
        filters={filters}
        onFiltersChange={handleFiltersChange}
        onClearFilters={handleClearFilters}
        loading={isLoading}
      />

      {/* Conversations list */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Conversations</CardTitle>
              <CardDescription>
                {conversationsData?.total ? (
                  `${conversationsData.total} conversation${conversationsData.total === 1 ? '' : 's'} found`
                ) : (
                  'Manage your WhatsApp conversations'
                )}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
              <p className="text-muted-foreground mt-4">Loading conversations...</p>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-error mb-4">Failed to load conversations</p>
              <Button variant="outline" onClick={() => window.location.reload()}>
                Retry
              </Button>
            </div>
          ) : !conversationsWithUnreadCounts.length ? (
            <div className="text-center py-12">
              <ChatBubbleLeftRightIcon className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground mb-4">
                {filters.search || Object.keys(filters).some(key => 
                  key !== 'page' && key !== 'per_page' && key !== 'sort_by' && key !== 'sort_order' && 
                  filters[key as keyof ConversationFilters]
                ) ? 'No conversations match your filters.' : 'No conversations yet.'}
              </p>
              {!filters.search && (
                <Button 
                  variant="outline"
                  onClick={() => setIsNewConversationModalOpen(true)}
                >
                  <PlusIcon className="w-4 h-4 mr-2" />
                  Start First Conversation
                </Button>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {conversationsWithUnreadCounts.map((conversation: Conversation) => {
                const assignedAgent = conversation.assigned_agent_id 
                  ? agentsMap.get(conversation.assigned_agent_id) 
                  : null;
                
                return (
                  <ConversationListItem
                    key={conversation._id}
                    conversation={conversation}
                    assignedAgent={assignedAgent}
                    agentsLoading={agentsLoading}
                    onClick={handleConversationClick}
                  />
                );
              })}

              {/* Pagination */}
              {conversationsData && (conversationsData.pages ?? 0) > 1 && (
                <div className="pt-4">
                  <Pagination
                    currentPage={conversationsData.page ?? 1}
                    totalPages={conversationsData.pages ?? 1}
                    totalItems={conversationsData.total ?? 0}
                    itemsPerPage={conversationsData.per_page ?? 20}
                    onPageChange={(page) => setFilters(prev => ({ ...prev, page }))}
                    disabled={isLoading}
                    showInfo={true}
                  />
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* New Conversation Modal */}
      <NewConversationModal
        isOpen={isNewConversationModalOpen}
        onClose={() => setIsNewConversationModalOpen(false)}
        onSuccess={() => {
          // Refresh conversations list after successful creation
          window.location.reload();
        }}
      />
    </div>
  );
}