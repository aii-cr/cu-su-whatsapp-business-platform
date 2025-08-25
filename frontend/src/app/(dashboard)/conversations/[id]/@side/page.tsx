"use client";

import { useParams } from 'next/navigation';
import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { httpClient } from '@/lib/http';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/feedback/LoadingSpinner';
import { formatMessageTime } from '@/lib/timezone';
import { useAuthStore } from '@/lib/store';
import { useHistoryPanel } from '@/hooks/useHistoryPanel';
import { 
  ClockIcon, 
  DocumentArrowDownIcon,
  DocumentTextIcon,
  UserIcon,
  ChatBubbleLeftRightIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  PaperAirplaneIcon,
  EyeSlashIcon,
  EyeIcon,
  ChevronDownIcon,
  FunnelIcon
} from '@heroicons/react/24/outline';

interface HistoryItem {
  type: string;
  ts_utc: string;
  actor_name?: string;
  actor_email?: string;
  payload: {
    text?: string;
    full_text?: string;
    direction?: string;
    message_type?: string;
    from?: string;
    to?: string;
    status?: string;
    reason?: string;
    participant_id?: string;
    role?: string;
    note_content?: string;
  };
  details?: string;
}

interface ExportModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  conversationId: string;
}

function getHistoryIcon(type: string) {
  switch (type) {
    case 'message_outbound':
      return <ChatBubbleLeftRightIcon className="w-4 h-4 text-blue-500" />;
    case 'message_inbound':
      return <ChatBubbleLeftRightIcon className="w-4 h-4 text-green-500" />;
    case 'message_sent':
    case 'message_received':
      return <ChatBubbleLeftRightIcon className="w-4 h-4 text-blue-500" />;
    case 'participant_added':
    case 'participant_removed':
      return <UserIcon className="w-4 h-4 text-green-500" />;
    case 'conversation_created':
      return <ClockIcon className="w-4 h-4 text-purple-500" />;
    case 'note_added':
      return <DocumentTextIcon className="w-4 h-4 text-purple-500" />;
    case 'conversation_accessed':
      return <EyeIcon className="w-4 h-4 text-gray-500" />;
    case 'status_changed':
      return <ExclamationTriangleIcon className="w-4 h-4 text-amber-500" />;
    default:
      return <ClockIcon className="w-4 h-4 text-muted-foreground" />;
  }
}

function getHistoryTitle(item: HistoryItem) {
  switch (item.type) {
    case 'message_sent':
      return 'Message Sent';
    case 'message_received':
      return 'Message Received';
    case 'participant_added':
      return 'Participant Added';
    case 'participant_removed':
      return 'Participant Removed';
    case 'conversation_created':
      return 'Conversation Created';
    case 'status_changed':
      return 'Status Changed';
    case 'note_added':
      return 'Note Added';
    case 'message_outbound':
      return 'Message Sent';
    case 'message_inbound':
      return 'Message Received';
    case 'conversation_accessed':
      return 'Conversation Accessed';
    default:
      return item.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }
}

function getHistoryDescription(item: HistoryItem) {
  switch (item.type) {
    case 'message_outbound':
    case 'message_inbound':
    case 'message_sent':
    case 'message_received':
      // Show message text or "Media message" for non-text messages
      if (item.payload.message_type !== 'text') {
        return 'Media message';
      }
      return item.payload.text ? `"${item.payload.text}"` : 'Message';
    case 'participant_added':
      return `${item.payload.participant_id} added as ${item.payload.role}`;
    case 'participant_removed':
      return `${item.payload.participant_id} removed`;
    case 'status_changed':
      return `Status changed to ${item.payload.status}`;
    case 'note_added':
      return item.payload.note_content || item.details || 'Note added';
    case 'conversation_accessed':
      return 'Conversation was accessed';
    default:
      return item.details || 'Activity recorded';
  }
}

// Export Modal Component
function ExportModal({ open, onOpenChange, conversationId }: ExportModalProps) {
  const [exportType, setExportType] = useState('all');
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    try {
      setIsExporting(true);
      
      // Use the httpClient with proper base URL construction
      const baseUrl = (httpClient as any).baseUrl || 'http://localhost:8010/api/v1';
      const exportUrl = `${baseUrl}/conversations/${conversationId}/history/export?export_type=${exportType}`;
      
      console.log('Attempting to export PDF from:', exportUrl);
      
      const res = await fetch(exportUrl, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Accept': 'application/pdf',
        },
      });
      
      if (!res.ok) {
        const errorText = await res.text();
        console.error('Export failed with status:', res.status, 'Error:', errorText);
        throw new Error(`Export failed: ${res.status} ${res.statusText}`);
      }
      
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `conversation-history-${conversationId}-${exportType}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      onOpenChange(false);
    } catch (error) {
      console.error('Error exporting PDF:', error);
      alert('Failed to export PDF. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className={`fixed inset-0 z-50 ${open ? 'block' : 'hidden'}`}>
      <div className="fixed inset-0 bg-black/50" onClick={() => onOpenChange(false)} />
      <div className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-background border border-border rounded-lg p-6 w-96">
        <h3 className="text-lg font-semibold mb-4">Export History</h3>
        
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">Export Type</label>
            <select 
              value={exportType}
              onChange={(e) => setExportType(e.target.value)}
              className="w-full p-2 border border-border rounded focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="all">All Activities</option>
              <option value="messages">Messages Only</option>
              <option value="transfers">Agent Transfers & Participants</option>
              <option value="actions">Conversation Actions</option>
            </select>
          </div>
          
          <div className="flex gap-2 pt-4">
            <Button
              onClick={handleExport}
              disabled={isExporting}
              className="flex-1"
            >
              {isExporting ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Exporting...
                </>
              ) : (
                <>
                  <DocumentArrowDownIcon className="w-4 h-4 mr-2" />
                  Export PDF
                </>
              )}
            </Button>
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isExporting}
            >
              Cancel
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function HistoryTimelinePanel() {
  const params = useParams();
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const { isHistoryVisible, setHistoryVisible } = useHistoryPanel();
  const id = params.id as string;
  
  // State management
  const [showExportModal, setShowExportModal] = useState(false);
  const [noteText, setNoteText] = useState('');
  const [includeAccessLogs, setIncludeAccessLogs] = useState(false);
  const [includeMessages, setIncludeMessages] = useState(false);
  const [showFilterMenu, setShowFilterMenu] = useState(false);

  // Data fetching
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['conversation', id, 'history', includeAccessLogs, includeMessages],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (includeAccessLogs) params.set('include_access_logs', 'true');
      if (includeMessages) params.set('include_messages', 'true');
      const queryString = params.toString() ? `?${params.toString()}` : '';
      const response = await httpClient.get<{ items: HistoryItem[] }>(`/conversations/${id}/history${queryString}`);
      return response;
    },
  });

  // Add note mutation
  const addNoteMutation = useMutation({
    mutationFn: async (note: string) => {
      return await httpClient.post(`/conversations/${id}/history/notes`, { note });
    },
    onSuccess: () => {
      setNoteText('');
      refetch(); // Refresh history to show new note
    },
    onError: (error) => {
      console.error('Failed to add note:', error);
    }
  });

  const handleAddNote = () => {
    if (noteText.trim()) {
      addNoteMutation.mutate(noteText.trim());
    }
  };

  const handleRefresh = () => {
    refetch();
  };

  // Close filter menu when clicking outside
  const handleClickOutside = (e: MouseEvent) => {
    const target = e.target as Element;
    if (showFilterMenu && !target.closest('.filter-menu')) {
      setShowFilterMenu(false);
    }
  };

  useEffect(() => {
    if (showFilterMenu) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showFilterMenu]);

  if (error) {
    return (
      <Card className="h-full">
        <CardContent className="p-6 text-center">
          <ExclamationTriangleIcon className="w-8 h-8 text-error mx-auto mb-2" />
          <p className="text-sm text-muted-foreground">Failed to load history</p>
          <Button 
            size="sm" 
            onClick={handleRefresh}
            className="mt-2"
          >
            <ArrowPathIcon className="w-4 h-4 mr-1" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card className="h-full flex flex-col">
        <CardHeader className="flex flex-col space-y-3 pb-4">
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <ClockIcon className="w-5 h-5 text-primary" />
            History Timeline
          </CardTitle>
          
          <div className="flex items-center gap-1 flex-wrap">
            <Button 
              size="sm" 
              variant="ghost"
              onClick={handleRefresh}
              disabled={isLoading}
              className="text-xs"
              title="Refresh history"
            >
              <ArrowPathIcon className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
            
            {/* Filter dropdown */}
            <div className="relative filter-menu">
              <Button 
                size="sm" 
                variant={(includeAccessLogs || includeMessages) ? "default" : "ghost"}
                onClick={() => setShowFilterMenu(!showFilterMenu)}
                className="text-xs"
                title="Filter timeline"
              >
                <FunnelIcon className="w-4 h-4" />
                <ChevronDownIcon className="w-3 h-3 ml-1" />
              </Button>
              
              {showFilterMenu && (
                <div className="absolute right-0 top-full mt-1 bg-background border border-border rounded-lg shadow-lg p-3 min-w-[180px] max-w-[250px] z-50 filter-menu">
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id="include-messages"
                        checked={includeMessages}
                        onChange={(e) => setIncludeMessages(e.target.checked)}
                        className="rounded border-border"
                      />
                      <label htmlFor="include-messages" className="text-sm">
                        Show Messages
                      </label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id="include-access-logs"
                        checked={includeAccessLogs}
                        onChange={(e) => setIncludeAccessLogs(e.target.checked)}
                        className="rounded border-border"
                      />
                      <label htmlFor="include-access-logs" className="text-sm">
                        Show Access Logs
                      </label>
                    </div>
                  </div>
                  <div className="mt-3 pt-2 border-t border-border">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setShowFilterMenu(false)}
                      className="w-full text-xs"
                    >
                      Close
                    </Button>
                  </div>
                </div>
              )}
            </div>
            
            <Button 
              size="sm" 
              variant="outline"
              onClick={() => setShowExportModal(true)}
              className="text-xs"
              disabled={isLoading || !data?.items?.length}
            >
              <DocumentArrowDownIcon className="w-4 h-4 mr-1" />
              <span className="hidden sm:inline">Export</span>
            </Button>
            
            <Button 
              size="sm" 
              variant="ghost"
              onClick={() => setHistoryVisible(!isHistoryVisible)}
              className="text-xs"
              title={isHistoryVisible ? "Hide history" : "Show history"}
            >
              {isHistoryVisible ? <EyeSlashIcon className="w-4 h-4" /> : <EyeIcon className="w-4 h-4" />}
            </Button>
          </div>
        </CardHeader>
        
        {isHistoryVisible && (
          <>
            {/* History Content */}
            <CardContent className="flex-1 overflow-y-auto px-4 pb-4">
              {isLoading ? (
                <div className="flex items-center justify-center h-32">
                  <LoadingSpinner size="sm" text="Loading history..." />
                </div>
              ) : !data?.items?.length ? (
                <div className="text-center py-8">
                  <ClockIcon className="w-12 h-12 text-muted-foreground mx-auto mb-3 opacity-50" />
                  <p className="text-sm text-muted-foreground">No activity recorded yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {data.items.map((item, index) => {
                    const isMessageType = item.type.includes('message');
                    const isParticipantType = item.type.includes('participant');
                    const isStatusType = item.type.includes('status') || item.type.includes('conversation');
                    const isNoteType = item.type.includes('note');
                    
                    return (
                      <div key={`${item.ts_utc}-${index}`} className="relative pl-8 pb-3 last:pb-0">
                        {/* Timeline line */}
                        {index < data.items.length - 1 && (
                          <div className="absolute left-[11px] top-8 bottom-0 w-0.5 bg-gradient-to-b from-border via-border/50 to-transparent" />
                        )}
                        
                        {/* Timeline dot with enhanced styling */}
                        <div className={`absolute left-0 top-1 w-6 h-6 rounded-full flex items-center justify-center border-2 shadow-sm transition-all
                          ${isMessageType ? 'bg-blue-50 border-blue-200 dark:bg-blue-950 dark:border-blue-800' :
                            isParticipantType ? 'bg-green-50 border-green-200 dark:bg-green-950 dark:border-green-800' :
                            isStatusType ? 'bg-amber-50 border-amber-200 dark:bg-amber-950 dark:border-amber-800' :
                            isNoteType ? 'bg-purple-50 border-purple-200 dark:bg-purple-950 dark:border-purple-800' :
                            'bg-gray-50 border-gray-200 dark:bg-gray-950 dark:border-gray-800'
                          }`}>
                          {getHistoryIcon(item.type)}
                        </div>
                        
                        {/* Content with enhanced WhatsApp-style card */}
                        <div className={`p-3 rounded-lg border transition-all hover:shadow-sm
                          ${isMessageType ? 'bg-blue-50/50 border-blue-100 dark:bg-blue-950/30 dark:border-blue-900/50' :
                            isParticipantType ? 'bg-green-50/50 border-green-100 dark:bg-green-950/30 dark:border-green-900/50' :
                            isStatusType ? 'bg-amber-50/50 border-amber-100 dark:bg-amber-950/30 dark:border-amber-900/50' :
                            isNoteType ? 'bg-purple-50/50 border-purple-100 dark:bg-purple-950/30 dark:border-purple-900/50' :
                            'bg-surface/50 border-border/50'
                          }`}>
                          <div className="flex items-start justify-between gap-2 mb-2">
                            <h4 className="text-sm font-medium text-foreground flex items-center gap-2">
                              <span className="text-xs">{getHistoryIcon(item.type)}</span>
                              {getHistoryTitle(item)}
                            </h4>
                            <time className="text-xs text-muted-foreground whitespace-nowrap">
                              {formatMessageTime(item.ts_utc)}
                            </time>
                          </div>
                          
                          <div className="text-xs text-muted-foreground leading-relaxed mb-2">
                            {getHistoryDescription(item)}
                          </div>
                          
                          {/* Show actor information */}
                          {(item.actor_name || item.actor_email) && (
                            <div className="text-xs text-muted-foreground">
                              <span className="font-medium">By:</span> {item.actor_name}
                              {item.actor_email && ` (${item.actor_email})`}
                            </div>
                          )}
                          
                          {/* Additional details for specific event types */}
                          {item.type === 'message_sent' && item.payload.to && (
                            <div className="mt-2 text-xs text-muted-foreground">
                              <span className="font-medium">To:</span> {item.payload.to}
                            </div>
                          )}
                          
                          {item.type === 'message_received' && item.payload.from && (
                            <div className="mt-2 text-xs text-muted-foreground">
                              <span className="font-medium">From:</span> {item.payload.from}
                            </div>
                          )}
                          
                          {item.type === 'status_changed' && item.payload.reason && (
                            <div className="mt-2 text-xs text-muted-foreground">
                              <span className="font-medium">Reason:</span> {item.payload.reason}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>

            {/* Add Note Section */}
            <div className="border-t border-border p-4 bg-surface/50">
              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground">Add Note</label>
                <div className="flex gap-2">
                  <Input
                    value={noteText}
                    onChange={(e) => setNoteText(e.target.value)}
                    placeholder="Leave a note for this conversation..."
                    className="flex-1 text-sm"
                    maxLength={1000}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleAddNote();
                      }
                    }}
                  />
                  <Button
                    size="sm"
                    onClick={handleAddNote}
                    disabled={!noteText.trim() || addNoteMutation.isPending}
                    className="px-3"
                  >
                    {addNoteMutation.isPending ? (
                      <LoadingSpinner size="sm" />
                    ) : (
                      <PaperAirplaneIcon className="w-4 h-4" />
                    )}
                  </Button>
                </div>
                {noteText.length > 800 && (
                  <div className="text-xs text-muted-foreground">
                    {noteText.length}/1000 characters
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </Card>

      {/* Export Modal */}
      <ExportModal 
        open={showExportModal} 
        onOpenChange={setShowExportModal} 
        conversationId={id} 
      />
    </>
  );
}
