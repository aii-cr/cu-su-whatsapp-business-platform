/**
 * Conversation header component with customer info and actions.
 * Displays customer details, conversation status, and action buttons.
 */

import * as React from 'react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Avatar } from '@/components/ui/Avatar';
import { formatRelativeTime } from '@/lib/utils';
import { Conversation } from '@/features/conversations/models/conversation';
import { 
  ArrowLeftIcon,
  PhoneIcon,
  VideoCameraIcon,
  EllipsisVerticalIcon,
  InformationCircleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { TagIcon } from '@heroicons/react/24/outline';
import { useState } from 'react';
import { ParticipantsModal } from './ParticipantsModal';
import { useHistoryPanel } from '@/hooks/useHistoryPanel';
import { ConversationTagsBar } from '@/features/tags/components/ConversationTagsBar';
import { EditTagsModal } from '@/features/tags/components/EditTagsModal';
import { useConversationTags } from '@/features/tags/hooks/useConversationTags';
import { DropdownMenu, DropdownMenuItem } from '@/components/ui/DropdownMenu';
import { useAuthStore } from '@/lib/store';
import { toast } from '@/components/feedback/Toast';
import { ConversationsApi } from '@/features/conversations/api/conversationsApi';
import { useQueryClient } from '@tanstack/react-query';

export interface ConversationHeaderProps {
  conversation: Conversation;
  onBack?: () => void;
  onCall?: () => void;
  onVideoCall?: () => void;
  onMoreActions?: () => void;
  onViewInfo?: () => void;
  className?: string;
}

const ConversationHeader = React.forwardRef<HTMLDivElement, ConversationHeaderProps>(
  ({ 
    conversation, 
    onBack, 
    onCall, 
    onVideoCall, 
    onMoreActions, 
    onViewInfo,
    className = ''
  }, ref) => {
    const { user } = useAuthStore();
    const queryClient = useQueryClient();
    const [isClaiming, setIsClaiming] = useState(false);
    const getStatusVariant = (status: string) => {
      switch (status) {
        case 'active':
          return 'success';
        case 'pending':
          return 'warning';
        case 'closed':
          return 'secondary';
        default:
          return 'secondary';
      }
    };

    const [showParticipants, setShowParticipants] = useState(false);
    const [showEditTags, setShowEditTags] = useState(false);
    const { isHistoryVisible, setHistoryVisible } = useHistoryPanel();
    
    const handleClaimConversation = async () => {
      if (!user) {
        toast.error('You must be logged in to claim conversations');
        return;
      }

      if (isClaiming) return;

      try {
        setIsClaiming(true);
        await ConversationsApi.claimConversation(String(conversation._id));
        toast.success('Conversation claimed successfully! You have been assigned to this chat.');
        
        // Invalidate and refetch conversation data instead of reloading
        queryClient.invalidateQueries({ queryKey: ['conversations', 'detail', String(conversation._id)] });
        queryClient.invalidateQueries({ queryKey: ['conversations', 'list'] });
      } catch (error) {
        console.error('Error claiming conversation:', error);
        toast.error('Failed to claim conversation. Please try again.');
      } finally {
        setIsClaiming(false);
      }
    };
    
    // Get conversation tags
    const { data: conversationTags } = useConversationTags(String(conversation._id));
    
    return (
      <div 
        ref={ref}
        className={`flex items-center justify-between p-4 border-b border-border bg-surface ${className}`}
      >
        <div className="flex items-center space-x-3 flex-1 min-w-0">
          {onBack && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onBack}
              className="mr-2 flex-shrink-0"
              aria-label="Go back"
            >
              <ArrowLeftIcon className="w-5 h-5" />
            </Button>
          )}
          
          <Avatar
            src={conversation.customer?.avatar_url}
            fallback={
              conversation.customer?.name?.charAt(0) || 
              conversation.customer_name?.charAt?.(0) ||
              conversation.customer?.phone?.slice(-2) ||
              conversation.customer_phone?.slice(-2) || 
              'C'
            }
            size="md"
            className="flex-shrink-0 cursor-pointer"
            onClick={onViewInfo}
          />
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-1">
              <h1 className="text-lg font-semibold truncate">
                {conversation.customer?.name || conversation.customer_name || conversation.customer?.phone || conversation.customer_phone || 'Unknown Customer'}
              </h1>
              <Badge 
                variant={getStatusVariant(conversation.status)}
                className="text-xs flex-shrink-0"
              >
                {conversation.status}
              </Badge>
            </div>
            
            <div className="flex items-center space-x-2 text-sm text-muted-foreground mb-2">
              <span className="truncate">
                {(conversation.customer?.phone || conversation.customer_phone) && `${conversation.customer?.phone || conversation.customer_phone} • `}
                Last seen {formatRelativeTime(conversation.updated_at)}
              </span>
            </div>
            
            {/* Tags */}
            <div className="mt-2">
              <ConversationTagsBar
                conversationId={String(conversation._id)}
                tags={conversationTags?.map(ct => ({
                  ...ct.tag,
                  usage_count: 0, // Default value since ConversationTag doesn't include usage_count
                })) || []}
                maxDisplay={5}
                onEdit={() => setShowEditTags(true)}
                size="sm"
              />
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center space-x-1 md:space-x-2 flex-shrink-0">
          {/* Claim button for unassigned conversations */}
          {!conversation.assigned_agent_id && user && (
            <Button 
              variant="default" 
              size="sm" 
              onClick={handleClaimConversation}
              disabled={isClaiming}
              className="text-xs md:text-sm px-2 md:px-3 bg-primary hover:bg-primary/90"
              title="Claim this conversation"
            >
              {isClaiming ? 'Claiming...' : 'Claim Chat'}
            </Button>
          )}
          
          {/* Show History button when hidden */}
          {!isHistoryVisible && (
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setHistoryVisible(true)}
              className="text-xs md:text-sm px-2 md:px-3"
              title="Show history timeline"
            >
              <ClockIcon className="w-4 h-4 mr-1" />
              <span className="hidden sm:inline">History</span>
            </Button>
          )}
          
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => setShowParticipants(true)}
            className="text-xs md:text-sm px-2 md:px-3"
          >
            <span className="hidden sm:inline">Participants</span>
            <span className="sm:hidden">👥</span>
          </Button>
          {onCall && (
            <Button 
              variant="ghost" 
              size="icon"
              onClick={onCall}
              aria-label="Voice call"
            >
              <PhoneIcon className="w-5 h-5" />
            </Button>
          )}
          
          {onVideoCall && (
            <Button 
              variant="ghost" 
              size="icon"
              onClick={onVideoCall}
              aria-label="Video call"
            >
              <VideoCameraIcon className="w-5 h-5" />
            </Button>
          )}
          
          {onViewInfo && (
            <Button 
              variant="ghost" 
              size="icon"
              onClick={onViewInfo}
              aria-label="View contact info"
            >
              <InformationCircleIcon className="w-5 h-5" />
            </Button>
          )}
          
          <DropdownMenu
            trigger={
              <Button 
                variant="outline" 
                size="icon"
                className="bg-background border-border hover:bg-accent hover:border-border text-foreground"
                aria-label="More actions"
              >
                <EllipsisVerticalIcon className="w-5 h-5" />
              </Button>
            }
            align="right"
          >
            <DropdownMenuItem onClick={() => setShowEditTags(true)}>
              <div className="flex items-center gap-2">
                <TagIcon className="h-4 w-4" />
                Edit Tags
              </div>
            </DropdownMenuItem>
            {onMoreActions && (
              <DropdownMenuItem onClick={onMoreActions}>
                More Options
              </DropdownMenuItem>
            )}
          </DropdownMenu>
        </div>
        
        {/* Modals */}
        <ParticipantsModal 
          open={showParticipants} 
          onOpenChange={setShowParticipants} 
          conversationId={String(conversation._id)} 
          canWrite={true} 
        />
        <EditTagsModal
          open={showEditTags}
          onOpenChange={setShowEditTags}
          conversationId={String(conversation._id)}
        />
      </div>
    );
  }
);
ConversationHeader.displayName = 'ConversationHeader';

export { ConversationHeader };