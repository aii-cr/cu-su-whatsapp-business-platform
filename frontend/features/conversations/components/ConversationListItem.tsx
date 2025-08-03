/**
 * Conversation list item component with comprehensive display.
 * Shows customer info, assignment details, status, and allows navigation.
 */

'use client';

import { useRouter } from 'next/navigation';
import { Avatar } from '@/components/ui/Avatar';
import { Badge } from '@/components/ui/Badge';
import { Conversation } from '../models/conversation';
import { formatRelativeTime, truncateText } from '@/lib/utils';
import { useAuthStore } from '@/lib/store';
import { useUser, getUserDisplayName, getUserFullName } from '@/features/users/hooks/useUsers';
import { 
  UserIcon,
  BuildingOfficeIcon,
  PhoneIcon,
  ChatBubbleLeftRightIcon,
  ClockIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';

interface ConversationListItemProps {
  conversation: Conversation;
  onClick?: (conversation: Conversation) => void;
  className?: string;
}

export function ConversationListItem({ 
  conversation, 
  onClick,
  className = '' 
}: ConversationListItemProps) {
  const router = useRouter();

  const handleClick = () => {
    if (onClick) {
      onClick(conversation);
    } else {
      // Default navigation to conversation details
      router.push(`/conversations/${conversation._id}`);
    }
  };

  // Status color mapping
  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'pending':
      case 'waiting':
        return 'warning';
      case 'closed':
        return 'secondary';
      case 'transferred':
        return 'outline';
      default:
        return 'secondary';
    }
  };

  // Priority color mapping
  const getPriorityVariant = (priority: string) => {
    switch (priority) {
      case 'urgent':
      case 'high':
        return 'destructive';
      case 'medium':
        return 'warning';
      case 'low':
        return 'outline';
      default:
        return 'secondary';
    }
  };

  // Get customer display name
  const customerName = conversation.customer?.name || 
                      conversation.customer_name || 
                      conversation.customer?.phone || 
                      conversation.customer_phone || 
                      'Unknown Customer';

  // Get customer phone
  const customerPhone = conversation.customer?.phone || conversation.customer_phone;

  // Fetch assigned agent information
  const { data: assignedAgentUser } = useUser(conversation.assigned_agent_id);
  
  // Get assigned agent info with proper name lookup
  const assignedAgent = conversation.assigned_agent_id ? {
    id: conversation.assigned_agent_id,
    name: assignedAgentUser ? getUserDisplayName(assignedAgentUser) : `Agent ${conversation.assigned_agent_id.slice(-4)}`,
  } : null;

  // Get department info (placeholder - would need to load from department API)
  const department = conversation.department_id ? {
    id: conversation.department_id,
    name: `Dept ${conversation.department_id.slice(-4)}`, // Placeholder
  } : null;

  return (
    <div
      onClick={handleClick}
      className={`
        flex items-center p-4 border border-border rounded-lg 
        hover:bg-accent hover:text-accent-foreground 
        cursor-pointer transition-all duration-150 
        group relative
        ${className}
      `}
    >
      {/* Customer Avatar */}
      <div className="relative">
        <Avatar
          src={conversation.customer?.avatar_url || ''}
          fallback={customerName}
          size="md"
          className="mr-4"
        />
        
        {/* Unread indicator on avatar */}
        {conversation.unread_count > 0 && (
          <div className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full min-w-4 h-4 flex items-center justify-center text-xs font-medium border border-background">
            {conversation.unread_count > 99 ? '99+' : conversation.unread_count}
          </div>
        )}
      </div>

      {/* Main content */}
      <div className="flex-1 min-w-0">
        {/* Top row: Customer name and timestamp */}
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center space-x-2 min-w-0">
            <h3 className="font-medium text-foreground truncate">
              {customerName}
            </h3>
            
            {customerPhone && (
              <div className="flex items-center text-muted-foreground">
                <PhoneIcon className="w-3 h-3 mr-1" />
                <span className="text-xs">{customerPhone}</span>
              </div>
            )}
          </div>
          
          <span className="text-xs text-muted-foreground whitespace-nowrap ml-2">
            {formatRelativeTime(conversation.updated_at)}
          </span>
        </div>
        
        {/* Last message preview */}
        {conversation.last_message && (
          <p className="text-sm text-muted-foreground truncate mb-2">
            {conversation.last_message.sender_type === 'customer' ? (
              <ChatBubbleLeftRightIcon className="w-3 h-3 inline mr-1" />
            ) : (
              <span className="text-xs font-medium mr-1">You: </span>
            )}
            {truncateText(conversation.last_message.content, 60)}
          </p>
        )}
        
        {/* Status and priority badges */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 flex-wrap">
            <Badge 
              variant={getStatusVariant(conversation.status)}
              className="text-xs"
            >
              {conversation.status}
            </Badge>
            
            {conversation.priority !== 'medium' && (
              <Badge 
                variant={getPriorityVariant(conversation.priority)}
                className="text-xs"
              >
                {conversation.priority === 'urgent' && <ExclamationCircleIcon className="w-3 h-3 mr-1" />}
                {conversation.priority}
              </Badge>
            )}
            
            {conversation.channel && conversation.channel !== 'whatsapp' && (
              <Badge variant="outline" className="text-xs">
                {conversation.channel}
              </Badge>
            )}
          </div>
          
          {/* Assignment and department info */}
          <div className="flex flex-col items-end space-y-1 text-right">
            {/* Assigned agent */}
            {assignedAgent && assignedAgentUser && (
              <div className="flex items-center space-x-2 text-foreground" title={`Assigned to: ${assignedAgent.name}`}>
                <UserIcon className="w-4 h-4 text-primary" />
                <div className="text-right">
                  <div className="text-sm font-semibold leading-tight">
                    {getUserFullName(assignedAgentUser)}
                  </div>
                  <div className="text-xs text-muted-foreground leading-tight">
                    {assignedAgentUser.email}
                  </div>
                </div>
              </div>
            )}
            
            {/* Fallback for when user data is loading */}
            {assignedAgent && !assignedAgentUser && (
              <div className="flex items-center space-x-1 text-foreground" title={`Assigned to: ${assignedAgent.name}`}>
                <UserIcon className="w-4 h-4 text-primary" />
                <span className="text-sm font-medium">{assignedAgent.name}</span>
              </div>
            )}
            
            {/* Department */}
            {department && (
              <div className="flex items-center space-x-1 text-muted-foreground" title={`Department: ${department.name}`}>
                <BuildingOfficeIcon className="w-3 h-3" />
                <span className="text-xs">{department.name}</span>
              </div>
            )}
            
            {/* Unassigned indicator */}
            {!assignedAgent && (
              <div className="flex items-center space-x-1 text-muted-foreground" title="Unassigned">
                <UserIcon className="w-4 h-4 text-warning" />
                <span className="text-sm font-medium text-warning">Unassigned</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Hover indicator */}
      <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-150 ml-2">
        <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </div>
  );
}