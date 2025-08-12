"use client";

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { ParticipantIn, ParticipantOut, ParticipantRole, ParticipantInSchema, ParticipantOutSchema } from '../schemas/participants';
import { z } from 'zod';
import { httpClient } from '@/lib/http';

function useParticipants(conversationId: string) {
  return useQuery({
    queryKey: ['conversation', conversationId, 'participants'],
    queryFn: async (): Promise<{ items: ParticipantOut[] }> => {
      const res = await httpClient.get<{ items: unknown }>(`/conversations/${conversationId}/participants`);
      const parsed = z.object({ items: z.array(ParticipantOutSchema) }).parse(res);
      return parsed as { items: ParticipantOut[] };
    },
  });
}

export function ParticipantsPanel({ conversationId, canWrite }: { conversationId: string; canWrite: boolean }) {
  const qc = useQueryClient();
  const { data } = useParticipants(conversationId);
  const [userId, setUserId] = useState('');
  const [role, setRole] = useState<z.infer<typeof ParticipantRole>>('agent');

  const addMutation = useMutation({
    mutationFn: async (p: ParticipantIn) => {
      const body = ParticipantInSchema.parse(p);
      await httpClient.post(`/conversations/${conversationId}/participants`, body);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['conversation', conversationId, 'participants'] }),
  });

  const removeMutation = useMutation({
    mutationFn: async (participantId: string) => {
      await httpClient.delete(`/conversations/${conversationId}/participants/${participantId}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['conversation', conversationId, 'participants'] }),
  });

  const changeRoleMutation = useMutation({
    mutationFn: async ({ participantId, newRole }: { participantId: string; newRole: string }) => {
      await httpClient.patch(`/conversations/${conversationId}/participants/${participantId}`, { role: newRole });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['conversation', conversationId, 'participants'] }),
  });

  const items = data?.items ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Participants</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2">
          {items.map((p) => (
            <li key={p._id} className="flex items-center justify-between">
              <div className="text-sm">
                <div className="font-medium">{p.user_id}</div>
                <div className="text-muted-foreground">{p.role}</div>
              </div>
              <div className="flex gap-2">
                <select
                  className="border rounded px-2 py-1 text-sm"
                  value={p.role}
                  disabled={!canWrite}
                  onChange={(e) => changeRoleMutation.mutate({ participantId: p._id, newRole: e.target.value })}
                >
                  {['primary', 'agent', 'observer'].map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
                <Button variant="outline" size="sm" disabled={!canWrite} onClick={() => removeMutation.mutate(p._id)}>
                  Remove
                </Button>
              </div>
            </li>
          ))}
        </ul>

        <div className="mt-4 flex gap-2 items-center">
          <input
            className="border rounded px-2 py-1 text-sm flex-1"
            placeholder="User ID"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            disabled={!canWrite}
          />
          <select className="border rounded px-2 py-1 text-sm" value={role} onChange={(e) => setRole(e.target.value as any)} disabled={!canWrite}>
            {['primary', 'agent', 'observer'].map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
          <Button size="sm" disabled={!canWrite || !userId} onClick={() => addMutation.mutate({ user_id: userId, role })}>
            Add
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}


