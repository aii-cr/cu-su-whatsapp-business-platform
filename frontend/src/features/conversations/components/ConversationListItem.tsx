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
import { User, getUserDisplayName, getUserFullName } from '@/features/users/hooks/useUsers';
import { 
  UserIcon,
  BuildingOfficeIcon,
  PhoneIcon,
  ChatBubbleLeftRightIcon,
  ClockIcon,
  ExclamationCircleIcon,
  EllipsisVerticalIcon,
  TagIcon
} from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/Button';
import { TagList } from '@/features/tags';
import { EditTagsModal } from '@/features/tags/components/EditTagsModal';
import { useState, useEffect, useRef } from 'react';

interface ConversationListItemProps {
  conversation: Conversation;
  onClick?: (conversation: Conversation) => void;
  className?: string;
  assignedAgent?: User | null;
  agentsLoading?: boolean;
}

export function ConversationListItem({ 
  conversation, 
  onClick,
  className = '',
  assignedAgent,
  agentsLoading = false
}: ConversationListItemProps) {
  const router = useRouter();
  const [showEditTags, setShowEditTags] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside or pressing Escape
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setShowDropdown(false);
      }
    };

    if (showDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
        document.removeEventListener('keydown', handleKeyDown);
      };
    }
  }, [showDropdown]);

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

  // Get assigned agent info - now passed as prop
  const assignedAgentInfo = conversation.assigned_agent_id ? {
    id: conversation.assigned_agent_id,
    name: assignedAgent ? getUserDisplayName(assignedAgent) : `Agent ${conversation.assigned_agent_id.slice(-4)}`,
    user: assignedAgent
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
        group relative overflow-visible
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
        
        {/* Tags */}
        {conversation.tags && conversation.tags.length > 0 ? (
          <div className="mb-2">
            <TagList 
              tags={conversation.tags}
              variant="compact"
              size="sm"
              maxDisplay={4}
              className="gap-1"
            />
          </div>
        ) : (
          <div className="mb-2 text-xs text-muted-foreground">
            No tags assigned
          </div>
        )}
        
        {/* Status, priority, and participants */}
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
            {conversation.participants?.length ? (
              <Badge variant="outline" className="text-xs">
                {conversation.participants.length} participants
              </Badge>
            ) : null}
          </div>
          
          {/* Assignment and department info */}
          <div className="flex flex-col items-end space-y-1 text-right">
            {/* Assigned agent */}
            {assignedAgentInfo && assignedAgentInfo.user && (
              <div className="flex items-center space-x-2 text-foreground" title={`Assigned to: ${assignedAgentInfo.name}`}>
                <UserIcon className="w-4 h-4 text-primary" />
                <div className="text-right">
                  <div className="text-sm font-semibold leading-tight">
                    {getUserFullName(assignedAgentInfo.user)}
                  </div>
                  <div className="text-xs text-muted-foreground leading-tight">
                    {assignedAgentInfo.user.email}
                  </div>
                </div>
              </div>
            )}
            
            {/* Fallback for when user data is loading or failed to load */}
            {assignedAgentInfo && !assignedAgentInfo.user && (
              <div className="flex items-center space-x-1 text-foreground" title={`Assigned to: ${assignedAgentInfo.name}`}>
                <UserIcon className="w-4 h-4 text-primary" />
                <span className="text-sm font-medium">
                  {agentsLoading ? 'Loading...' : assignedAgentInfo.name}
                </span>
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
            {!assignedAgentInfo && (
              <div className="flex items-center space-x-1 text-muted-foreground" title="Unassigned">
                <UserIcon className="w-4 h-4 text-warning" />
                <span className="text-sm font-medium text-warning">Unassigned</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Three dots menu - always visible */}
      <div className="ml-2 flex items-center relative" ref={dropdownRef}>
        <div 
          onClick={(e) => {
            e.stopPropagation();
            setShowDropdown(!showDropdown);
          }}
          className="h-10 w-10 p-0 bg-muted hover:bg-accent text-foreground border border-border rounded-md flex items-center justify-center cursor-pointer transition-colors"
          aria-label="More actions"
        >
          <EllipsisVerticalIcon className="w-5 h-5" />
        </div>
        
        {/* Dropdown menu */}
        {showDropdown && (
          <div className="absolute right-0 top-full mt-1 z-[9999] min-w-[160px] bg-popover border border-border rounded-md shadow-lg">
            <div className="py-1">
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowDropdown(false);
                  setShowEditTags(true);
                }}
                className="w-full px-3 py-2 text-left text-sm transition-colors hover:bg-accent focus:bg-accent focus:outline-none flex items-center gap-2"
                role="menuitem"
              >
                <TagIcon className="h-4 w-4" />
                Edit Tags
              </button>
            </div>
          </div>
        )}
      </div>
      
      {/* Edit Tags Modal */}
      <EditTagsModal
        open={showEditTags}
        onOpenChange={setShowEditTags}
        conversationId={conversation._id}
      />
    </div>
  );
}