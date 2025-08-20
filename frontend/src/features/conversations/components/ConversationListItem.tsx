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
  EllipsisHorizontalIcon,
  TagIcon
} from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/Button';
import { TagList } from '@/features/tags';
import { EditTagsModal } from '@/features/tags/components/EditTagsModal';
import { useState, useEffect, useRef, useMemo } from 'react';
import { toast } from '@/components/feedback/Toast';
import { ConversationsApi } from '../api/conversationsApi';

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
  const { user } = useAuthStore();
  const [showEditTags, setShowEditTags] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [isClaiming, setIsClaiming] = useState(false);
  const [windowWidth, setWindowWidth] = useState(0);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Responsive tag display count
  const maxTagDisplay = useMemo(() => {
    if (windowWidth >= 1024) return 6; // lg screens
    if (windowWidth >= 768) return 4;  // md screens
    return 2; // sm screens and below
  }, [windowWidth]);

  // Handle window resize for responsive tag display
  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    handleResize(); // Set initial width
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

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

  const handleClaimConversation = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!user) {
      toast.error('You must be logged in to claim conversations');
      return;
    }

    setIsClaiming(true);
    try {
      await ConversationsApi.claimConversation(conversation._id);
      toast.success('Conversation claimed successfully');
    } catch (error) {
      console.error('Error claiming conversation:', error);
      toast.error('Failed to claim conversation');
    } finally {
      setIsClaiming(false);
    }
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'active': return 'default';
      case 'waiting': return 'warning';
      case 'closed': return 'secondary';
      default: return 'outline';
    }
  };

  const getPriorityVariant = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'destructive';
      case 'high': return 'warning';
      case 'low': return 'secondary';
      default: return 'outline';
    }
  };

  const customerName = conversation.customer?.name || 'Unknown Customer';
  const customerPhone = conversation.customer?.phone;
  
  const assignedAgentInfo = assignedAgent ? {
    user: assignedAgent,
    name: getUserDisplayName(assignedAgent)
  } : null;

  const department = conversation.department_id ? {
    id: conversation.department_id,
    name: `Dept ${conversation.department_id.slice(-4)}`, // Placeholder
  } : null;

  return (
    <div
      onClick={handleClick}
      className={`
        flex items-start p-3 sm:p-4 border border-border rounded-lg 
        hover:bg-accent hover:text-accent-foreground 
        cursor-pointer transition-all duration-150 
        group relative overflow-visible
        ${className}
      `}
    >
      {/* Customer Avatar */}
      <div className="relative flex-shrink-0">
        <Avatar
          src={conversation.customer?.avatar_url || ''}
          fallback={customerName}
          size="md"
          className="mr-3 sm:mr-4"
        />
      </div>
      
      {/* Unread indicator - positioned at top-left of conversation card */}
      {conversation.unread_count > 0 && (
        <div className="absolute -top-2 -left-2 bg-red-500 text-white rounded-full min-w-6 h-6 flex items-center justify-center text-sm font-bold border-2 border-background shadow-lg z-10">
          {conversation.unread_count > 99 ? '99+' : conversation.unread_count}
        </div>
      )}

      {/* Main content - responsive layout */}
      <div className="flex-1 min-w-0 overflow-hidden">
        {/* Mobile layout (stacked) */}
        <div className="block sm:hidden space-y-2">
          {/* Header: Name, Phone, Timestamp */}
          <div className="flex flex-col gap-1">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-foreground text-sm truncate flex-1">
                {customerName}
              </h3>
              <span className="text-xs text-muted-foreground whitespace-nowrap ml-2">
                {formatRelativeTime(conversation.updated_at)}
              </span>
            </div>
            
            {customerPhone && (
              <div className="flex items-center text-muted-foreground">
                <PhoneIcon className="w-3 h-3 mr-1 flex-shrink-0" />
                <span className="text-xs truncate">{customerPhone}</span>
              </div>
            )}
          </div>
          
          {/* Last message preview */}
          {conversation.last_message && (
            <div className="text-xs text-muted-foreground">
              {conversation.last_message.sender_type === 'customer' ? (
                <div className="flex items-center gap-1">
                  <ChatBubbleLeftRightIcon className="w-3 h-3 flex-shrink-0" />
                  <span className="truncate">
                    {truncateText(conversation.last_message.content, 40)}
                  </span>
                </div>
              ) : (
                <div className="flex items-center gap-1">
                  <span className="text-xs font-medium flex-shrink-0">You: </span>
                  <span className="truncate">
                    {truncateText(conversation.last_message.content, 40)}
                  </span>
                </div>
              )}
            </div>
          )}
          
          {/* Tags */}
          {conversation.tags && conversation.tags.length > 0 ? (
            <div>
              <TagList 
                tags={conversation.tags}
                variant="compact"
                size="sm"
                maxDisplay={2}
                showMore={true}
                className="gap-1"
              />
            </div>
          ) : (
            <div className="text-xs text-muted-foreground">
              No tags assigned
            </div>
          )}
          
          {/* Status and Priority Badges */}
          <div className="flex items-center gap-2 flex-wrap">
            <Badge 
              variant={getStatusVariant(conversation.status)}
              className="text-xs flex-shrink-0"
            >
              {conversation.status}
            </Badge>
            
            {conversation.priority !== 'medium' && (
              <Badge 
                variant={getPriorityVariant(conversation.priority)}
                className="text-xs flex-shrink-0"
              >
                {conversation.priority === 'urgent' && <ExclamationCircleIcon className="w-3 h-3 mr-1" />}
                {conversation.priority}
              </Badge>
            )}
          </div>
          
          {/* Assignment info - mobile */}
          <div className="flex flex-col items-start space-y-1 text-left">
            {assignedAgentInfo && assignedAgentInfo.user && (
              <div className="flex items-center gap-2 text-foreground" title={`Assigned to: ${assignedAgentInfo.name}`}>
                <UserIcon className="w-4 h-4 text-primary flex-shrink-0" />
                <div className="min-w-0">
                  <div className="text-xs font-semibold leading-tight truncate">
                    {getUserFullName(assignedAgentInfo.user)}
                  </div>
                  <div className="text-xs text-muted-foreground leading-tight truncate max-w-[150px]">
                    {assignedAgentInfo.user.email}
                  </div>
                </div>
              </div>
            )}
            
            {!assignedAgentInfo && (
              <div className="flex flex-col items-start gap-2">
                <div className="flex items-center gap-1 text-muted-foreground" title="Unassigned">
                  <UserIcon className="w-4 h-4 text-warning flex-shrink-0" />
                  <span className="text-xs font-medium text-warning">Unassigned</span>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleClaimConversation}
                  disabled={isClaiming}
                  className="text-xs px-2 py-1 h-7 w-full"
                >
                  {isClaiming ? 'Claiming...' : 'Claim'}
                </Button>
              </div>
            )}
          </div>
        </div>
        
        {/* Desktop layout (compact, space-efficient) */}
        <div className="hidden sm:flex sm:flex-col sm:justify-between h-full">
          {/* Top row: Customer name and timestamp */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-2 mb-2">
            <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2 min-w-0 flex-1">
              <h3 className="font-medium text-foreground truncate text-sm sm:text-base max-w-full min-w-0">
                {customerName}
              </h3>
              
              {customerPhone && (
                <div className="flex items-center text-muted-foreground flex-shrink-0">
                  <PhoneIcon className="w-3 h-3 mr-1 flex-shrink-0" />
                  <span className="text-xs truncate max-w-[120px]">{customerPhone}</span>
                </div>
              )}
            </div>
            
            <span className="text-xs text-muted-foreground whitespace-nowrap flex-shrink-0">
              {formatRelativeTime(conversation.updated_at)}
            </span>
          </div>
          
          {/* Last message preview */}
          {conversation.last_message && (
            <p className="text-xs sm:text-sm text-muted-foreground truncate mb-2 max-w-full">
              {conversation.last_message.sender_type === 'customer' ? (
                <ChatBubbleLeftRightIcon className="w-3 h-3 inline mr-1 flex-shrink-0" />
              ) : (
                <span className="text-xs font-medium mr-1 flex-shrink-0">You: </span>
              )}
              <span className="truncate">
                {truncateText(conversation.last_message.content, windowWidth >= 1024 ? 60 : windowWidth >= 768 ? 50 : 40)}
              </span>
            </p>
          )}
          
          {/* Tags */}
          {conversation.tags && conversation.tags.length > 0 ? (
            <div className="mb-2">
              <TagList 
                tags={conversation.tags}
                variant="compact"
                size="sm"
                maxDisplay={maxTagDisplay}
                showMore={true}
                className="gap-1"
              />
            </div>
          ) : (
            <div className="mb-2 text-xs text-muted-foreground">
              No tags assigned
            </div>
          )}
          
          {/* Status, priority, and participants */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-2">
            <div className="flex items-center gap-1 sm:gap-2 flex-wrap min-w-0">
              <Badge 
                variant={getStatusVariant(conversation.status)}
                className="text-xs flex-shrink-0"
              >
                {conversation.status}
              </Badge>
              
              {conversation.priority !== 'medium' && (
                <Badge 
                  variant={getPriorityVariant(conversation.priority)}
                  className="text-xs flex-shrink-0"
                >
                  {conversation.priority === 'urgent' && <ExclamationCircleIcon className="w-3 h-3 mr-1" />}
                  {conversation.priority}
                </Badge>
              )}
              
              {conversation.channel && conversation.channel !== 'whatsapp' && (
                <Badge variant="outline" className="text-xs flex-shrink-0">
                  {conversation.channel}
                </Badge>
              )}
              {conversation.participants?.length ? (
                <Badge variant="outline" className="text-xs flex-shrink-0">
                  {conversation.participants.length} participants
                </Badge>
              ) : null}
            </div>
            
            {/* Assignment and department info */}
            <div className="flex flex-col items-start sm:items-end space-y-1 text-left sm:text-right">
              {/* Assigned agent */}
              {assignedAgentInfo && assignedAgentInfo.user && (
                <div className="flex items-center gap-2 text-foreground" title={`Assigned to: ${assignedAgentInfo.name}`}>
                  <UserIcon className="w-4 h-4 text-primary flex-shrink-0" />
                  <div className="min-w-0">
                    <div className="text-xs sm:text-sm font-semibold leading-tight truncate">
                      {getUserFullName(assignedAgentInfo.user)}
                    </div>
                    <div className="text-xs text-muted-foreground leading-tight truncate max-w-[150px] sm:max-w-[200px]">
                      {assignedAgentInfo.user.email}
                    </div>
                  </div>
                </div>
              )}
              
              {/* Fallback for when user data is loading or failed to load */}
              {assignedAgentInfo && !assignedAgentInfo.user && (
                <div className="flex items-center gap-1 text-foreground" title={`Assigned to: ${assignedAgentInfo.name}`}>
                  <UserIcon className="w-4 h-4 text-primary flex-shrink-0" />
                  <span className="text-xs sm:text-sm font-medium truncate">
                    {agentsLoading ? 'Loading...' : assignedAgentInfo.name}
                  </span>
                </div>
              )}
              
              {/* Unassigned indicator with claim button */}
              {!assignedAgentInfo && (
                <div className="flex flex-col items-start sm:items-end gap-2">
                  <div className="flex items-center gap-1 text-muted-foreground" title="Unassigned">
                    <UserIcon className="w-4 h-4 text-warning flex-shrink-0" />
                    <span className="text-xs sm:text-sm font-medium text-warning">Unassigned</span>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleClaimConversation}
                    disabled={isClaiming}
                    className="text-xs px-2 py-1 h-7 w-full sm:w-auto"
                  >
                    {isClaiming ? 'Claiming...' : 'Claim'}
                  </Button>
                </div>
              )}
              
              {/* Department info - only show on larger screens */}
              {department && (
                <div className="hidden sm:flex items-center gap-1 text-muted-foreground" title={`Department: ${department.name}`}>
                  <BuildingOfficeIcon className="w-3 h-3 flex-shrink-0" />
                  <span className="text-xs truncate">{department.name}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Action menu - positioned absolutely */}
      <div className="absolute top-3 right-3">
        <div ref={dropdownRef} className="relative">
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              setShowDropdown(!showDropdown);
            }}
            className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <EllipsisVerticalIcon className="w-4 h-4" />
          </Button>
          
          {showDropdown && (
            <div className="absolute right-0 top-full mt-1 w-48 bg-background border border-border rounded-md shadow-lg z-20">
              <div className="py-1">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowEditTags(true);
                    setShowDropdown(false);
                  }}
                  className="w-full px-3 py-2 text-left text-sm hover:bg-accent flex items-center gap-2"
                >
                  <TagIcon className="w-4 h-4" />
                  Edit Tags
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    // Add more actions here
                    setShowDropdown(false);
                  }}
                  className="w-full px-3 py-2 text-left text-sm hover:bg-accent flex items-center gap-2"
                >
                  <EllipsisHorizontalIcon className="w-4 h-4" />
                  More Actions
                </button>
              </div>
            </div>
          )}
        </div>
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