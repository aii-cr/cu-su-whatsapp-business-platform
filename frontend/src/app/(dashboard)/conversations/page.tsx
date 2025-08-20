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
import { ConversationFilters as IConversationFilters, Conversation } from '@/features/conversations/models/conversation';
import { ConversationFilters as ConversationFiltersComponent } from '@/features/conversations/components/ConversationFilters';
import { ConversationListItem } from '@/features/conversations/components/ConversationListItem';
import { useUsers, User } from '@/features/users/hooks/useUsers';
import { useDashboardWebSocket } from '@/hooks/useDashboardWebSocket';
import { NewConversationModal } from '@/components/conversations/NewConversationModal';
import { 
  PlusIcon, 
  ChatBubbleLeftRightIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';

export default function ConversationsPage() {
  const { user } = useAuthStore();
  const [filters, setFilters] = useState<IConversationFilters>({
    page: 1,
    per_page: 20,
    sort_by: 'updated_at',
    sort_order: 'desc',
  });
  const [isNewConversationModalOpen, setIsNewConversationModalOpen] = useState(false);

  const { data: conversationsData, isLoading, error } = useConversations(filters);
  const { data: stats, isLoading: statsLoading } = useConversationStats();
  
  const { 
    isConnected: wsConnected, 
    getUnreadCount,
    getTotalUnreadCount,
    markConversationAsRead 
  } = useDashboardWebSocket();

  const assignedAgentIds = useMemo(() => {
    const list = conversationsData?.conversations ?? [];
    const uniqueIds = new Set<string>();
    list.forEach((conversation: Conversation) => {
      if (conversation.assigned_agent_id) uniqueIds.add(conversation.assigned_agent_id);
    });
    return Array.from(uniqueIds);
  }, [conversationsData?.conversations]);

  const { data: assignedAgents = [], isLoading: agentsLoading, error: agentsError } = useUsers(assignedAgentIds);

  const agentsMap = useMemo(() => {
    const map = new Map<string, User>();
    (assignedAgents as User[]).forEach((agent) => {
      map.set(agent._id, agent);
    });
    return map;
  }, [assignedAgents]);

  const conversationsWithUnreadCounts = useMemo(() => {
    const list = conversationsData?.conversations ?? [];
    return list.map((conversation: Conversation) => ({
      ...conversation,
      unread_count: getUnreadCount(conversation._id),
    }));
  }, [conversationsData?.conversations, getUnreadCount]);

  useEffect(() => {
    if (agentsError && assignedAgentIds.length > 0) {
      // toast.error('Failed to load agent information for conversations. Some agent names may not display correctly.');
      console.error('Failed to load agent information for conversations.');
    }
  }, [agentsError, assignedAgentIds.length]);

  const handleFiltersChange = (newFilters: IConversationFilters) => setFilters(newFilters);

  const handleClearFilters = () => setFilters({ page: 1, per_page: 20, sort_by: 'updated_at', sort_order: 'desc' });

  const handleConversationClick = (conversation: Conversation) => {
    if (getUnreadCount(conversation._id) > 0) {
      markConversationAsRead(conversation._id);
    }
    window.location.href = `/conversations/${conversation._id}`;
  };

  return (
    <div className="space-y-4 sm:space-y-6 px-4 sm:px-6">
      {/* Header Section - Mobile Responsive */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
            <h1 className="text-xl sm:text-2xl font-bold text-foreground">Conversations</h1>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-xs text-muted-foreground">{wsConnected ? 'Live' : 'Offline'}</span>
              {getTotalUnreadCount() > 0 && (
                <Badge variant="destructive" className="text-xs">
                  {getTotalUnreadCount()} unread
                </Badge>
              )}
            </div>
          </div>
          <p className="text-sm sm:text-base text-muted-foreground mt-1">
            Welcome back, {user ? getUserDisplayName(user) : 'User'}!
          </p>
        </div>
        <Button 
          onClick={() => setIsNewConversationModalOpen(true)}
          className="w-full sm:w-auto"
          size="sm"
        >
          <PlusIcon className="w-4 h-4 mr-2" />
          <span className="hidden sm:inline">New Conversation</span>
          <span className="sm:hidden">New</span>
        </Button>
      </div>

      {/* Stats Cards - Mobile Responsive Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <Card>
          <CardContent className="p-3 sm:p-4">
            <div className="flex items-center justify-between">
              <div className="min-w-0 flex-1">
                <p className="text-xs sm:text-sm text-muted-foreground truncate">Active</p>
                <p className="text-lg sm:text-2xl font-bold">{statsLoading ? '...' : stats?.active_conversations ?? 0}</p>
              </div>
              <ChatBubbleLeftRightIcon className="w-6 h-6 sm:w-8 sm:h-8 text-primary-500 flex-shrink-0" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-3 sm:p-4">
            <div className="flex items-center justify-between">
              <div className="min-w-0 flex-1">
                <p className="text-xs sm:text-sm text-muted-foreground truncate">Pending</p>
                <p className="text-lg sm:text-2xl font-bold">
                  {statsLoading ? '...' : ((stats?.total_conversations ?? 0) - (stats?.active_conversations ?? 0) - (stats?.closed_conversations ?? 0))}
                </p>
              </div>
              <ClockIcon className="w-6 h-6 sm:w-8 sm:h-8 text-warning flex-shrink-0" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-3 sm:p-4">
            <div className="flex items-center justify-between">
              <div className="min-w-0 flex-1">
                <p className="text-xs sm:text-sm text-muted-foreground truncate">Closed</p>
                <p className="text-lg sm:text-2xl font-bold">{statsLoading ? '...' : stats?.closed_conversations ?? 0}</p>
              </div>
              <Badge variant="secondary" className="text-xs flex-shrink-0">Today</Badge>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-3 sm:p-4">
            <div className="flex items-center justify-between">
              <div className="min-w-0 flex-1">
                <p className="text-xs sm:text-sm text-muted-foreground truncate">Avg Response</p>
                <p className="text-lg sm:text-2xl font-bold">{statsLoading ? '...' : `${Math.round(stats?.average_response_time_minutes ?? 0)}m`}</p>
              </div>
              <Badge variant="success" className="text-xs flex-shrink-0">↓ 30s</Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      <ConversationFiltersComponent
        filters={filters}
        onFiltersChange={handleFiltersChange}
        onClearFilters={handleClearFilters}
        loading={isLoading}
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Conversations</CardTitle>
              <CardDescription>
                {conversationsData?.total ? `${conversationsData.total} conversation${conversationsData.total === 1 ? '' : 's'} found` : 'Manage your WhatsApp conversations'}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto" />
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
              <p className="text-muted-foreground mb-4">{filters.search ? 'No conversations match your filters.' : 'No conversations yet.'}</p>
              {!filters.search && (
                <Button variant="outline" onClick={() => setIsNewConversationModalOpen(true)}>
                  Start First Conversation
                </Button>
              )}
            </div>
          ) : (
            <div className="space-y-2 sm:space-y-3">
              {conversationsWithUnreadCounts.map((conversation: Conversation) => {
                const assignedAgent = conversation.assigned_agent_id ? agentsMap.get(conversation.assigned_agent_id) ?? null : null;
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

              {conversationsData && (conversationsData.pages ?? 0) > 1 && (
                <div className="pt-4">
                  <Pagination
                    currentPage={conversationsData.page ?? 1}
                    totalPages={conversationsData.pages ?? 1}
                    totalItems={conversationsData.total ?? 0}
                    itemsPerPage={conversationsData.per_page ?? 20}
                    onPageChange={(page) => setFilters((prev) => ({ ...prev, page }))}
                    disabled={isLoading}
                    showInfo={true}
                  />
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <NewConversationModal
        isOpen={isNewConversationModalOpen}
        onClose={() => setIsNewConversationModalOpen(false)}
        onSuccess={() => window.location.reload()}
      />
    </div>
  );
}