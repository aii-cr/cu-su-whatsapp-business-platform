"use client";

import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/Dialog';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Avatar } from '@/components/ui/Avatar';
import { Badge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/feedback/LoadingSpinner';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { httpClient } from '@/lib/http';
import { z } from 'zod';
import { ParticipantOutSchema } from '../schemas/participants';
import { 
  UserIcon, 
  PlusIcon, 
  TrashIcon,
  UserPlusIcon,
  UsersIcon
} from '@heroicons/react/24/outline';

interface ParticipantsModalProps {
  open: boolean; 
  onOpenChange: (v: boolean) => void; 
  conversationId: string; 
  canWrite: boolean;
}

function getRoleColor(role: string) {
  switch (role) {
    case 'primary':
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    case 'agent':
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    case 'observer':
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  }
}

function getRoleIcon(role: string) {
  switch (role) {
    case 'primary':
      return '👑';
    case 'agent':
      return '💼';
    case 'observer':
      return '👀';
    default:
      return '👤';
  }
}

export function ParticipantsModal({ open, onOpenChange, conversationId, canWrite }: ParticipantsModalProps) {
  const qc = useQueryClient();
  const [newUserId, setNewUserId] = useState('');
  const [newUserRole, setNewUserRole] = useState<'primary' | 'agent' | 'observer'>('agent');
  const [isAdding, setIsAdding] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ['conversation', conversationId, 'participants'],
    queryFn: async () => {
      const res = await httpClient.get<{ items: unknown }>(`/conversations/${conversationId}/participants`);
      return z.object({ items: z.array(ParticipantOutSchema) }).parse(res);
    },
    enabled: open, // Only fetch when modal is open
  });

  const addMutation = useMutation({
    mutationFn: async ({ user_id, role }: { user_id: string; role: string }) => {
      await httpClient.post(`/conversations/${conversationId}/participants`, { user_id, role });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['conversation', conversationId, 'participants'] });
      setNewUserId('');
      setIsAdding(false);
    },
    onError: (error) => {
      console.error('Failed to add participant:', error);
    }
  });

  const removeMutation = useMutation({
    mutationFn: async (participantId: string) => {
      await httpClient.delete(`/conversations/${conversationId}/participants/${participantId}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['conversation', conversationId, 'participants'] }),
    onError: (error) => {
      console.error('Failed to remove participant:', error);
    }
  });

  const changeRoleMutation = useMutation({
    mutationFn: async ({ participantId, newRole }: { participantId: string; newRole: string }) => {
      return await httpClient.patch(`/conversations/${conversationId}/participants/${participantId}`, { role: newRole });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['conversation', conversationId, 'participants'] }),
    onError: (error) => {
      console.error('Failed to change role:', error);
    }
  });

  const handleAddParticipant = () => {
    if (newUserId.trim()) {
      addMutation.mutate({ user_id: newUserId.trim(), role: newUserRole });
    }
  };

  const participants = data?.items || [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md max-h-[80vh] flex flex-col">
        <DialogHeader className="flex flex-row items-center space-y-0 pb-4">
          <div className="flex items-center gap-2">
            <UsersIcon className="w-5 h-5 text-primary" />
            <DialogTitle className="text-lg font-semibold">
              Participants ({participants.length})
            </DialogTitle>
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-hidden flex flex-col space-y-4">
          {/* Participants List */}
          <div className="flex-1 overflow-y-auto space-y-3">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <LoadingSpinner size="sm" text="Loading participants..." />
              </div>
            ) : error ? (
              <div className="text-center py-8">
                <UserIcon className="w-8 h-8 text-error mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">Failed to load participants</p>
              </div>
            ) : participants.length === 0 ? (
              <div className="text-center py-8">
                <UserIcon className="w-12 h-12 text-muted-foreground mx-auto mb-3 opacity-50" />
                <p className="text-sm text-muted-foreground">No participants yet</p>
                <p className="text-xs text-muted-foreground mt-1">Add team members to collaborate</p>
              </div>
            ) : (
              <div className="space-y-2">
                {participants.map((participant) => (
                  <div 
                    key={participant._id} 
                    className="flex items-center justify-between p-3 bg-surface rounded-lg border border-border hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center space-x-3 flex-1 min-w-0">
                      <Avatar
                        fallback={participant.user_id.charAt(0).toUpperCase()}
                        size="sm"
                        className="flex-shrink-0"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium truncate">{participant.user_id}</p>
                          <span className="text-sm">{getRoleIcon(participant.role)}</span>
                        </div>
                        <Badge 
                          variant="secondary" 
                          className={`text-xs mt-1 ${getRoleColor(participant.role)}`}
                        >
                          {participant.role}
                        </Badge>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {canWrite && (
                        <>
                          <select
                            className="text-xs border border-border rounded px-2 py-1 bg-background"
                            value={participant.role}
                            onChange={(e) => changeRoleMutation.mutate({ 
                              participantId: participant._id, 
                              newRole: e.target.value 
                            })}
                            disabled={changeRoleMutation.isPending}
                          >
                            <option value="primary">Primary</option>
                            <option value="agent">Agent</option>
                            <option value="observer">Observer</option>
                          </select>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => removeMutation.mutate(participant._id)}
                            disabled={removeMutation.isPending}
                            className="text-error hover:bg-error/10 h-8 w-8"
                          >
                            <TrashIcon className="w-4 h-4" />
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Add Participant Section */}
          {canWrite && (
            <div className="border-t border-border pt-4 space-y-3">
              {!isAdding ? (
                <Button
                  variant="outline"
                  onClick={() => setIsAdding(true)}
                  className="w-full flex items-center gap-2"
                >
                  <UserPlusIcon className="w-4 h-4" />
                  Add Participant
                </Button>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Input
                      placeholder="Enter user ID"
                      value={newUserId}
                      onChange={(e) => setNewUserId(e.target.value)}
                      className="flex-1"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          handleAddParticipant();
                        } else if (e.key === 'Escape') {
                          setIsAdding(false);
                          setNewUserId('');
                        }
                      }}
                      autoFocus
                    />
                    <select
                      className="border border-border rounded px-3 py-2 bg-background text-sm min-w-[100px]"
                      value={newUserRole}
                      onChange={(e) => setNewUserRole(e.target.value as 'primary' | 'agent' | 'observer')}
                    >
                      <option value="agent">Agent</option>
                      <option value="primary">Primary</option>
                      <option value="observer">Observer</option>
                    </select>
                  </div>
                  
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={handleAddParticipant}
                      disabled={!newUserId.trim() || addMutation.isPending}
                      className="flex-1"
                    >
                      {addMutation.isPending ? (
                        <>
                          <LoadingSpinner size="sm" className="mr-2" />
                          Adding...
                        </>
                      ) : (
                        <>
                          <PlusIcon className="w-4 h-4 mr-2" />
                          Add
                        </>
                      )}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setIsAdding(false);
                        setNewUserId('');
                      }}
                      disabled={addMutation.isPending}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}


