'use client';

import { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useAuthStore } from '@/lib/store';
import { hasPermission, isSuperAdmin } from '@/lib/auth';
import { ConversationsApi } from '@/features/conversations/api/conversationsApi';
import { Conversation } from '@/features/conversations/models/conversation';
import { httpClient } from '@/lib/http';

export default function ArchivedConversationsPage() {
  const { user } = useAuthStore();
  const [items, setItems] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);

  const canRestore = hasPermission(user, 'conversation:restore') || isSuperAdmin(user);
  const canPurge = hasPermission(user, 'conversation:purge') || isSuperAdmin(user);

  const load = async () => {
    setLoading(true);
    try {
      const res = await ConversationsApi.getConversations({ is_archived: true, sort_by: 'updated_at', sort_order: 'desc' } as any);
      setItems(res.conversations as any);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const restore = async (id: string) => {
    await httpClient.post(`/conversations/${id}/restore`);
    await load();
  };

  const purge = async (id: string) => {
    if (!confirm('This will permanently delete this conversation. Continue?')) return;
    await httpClient.delete(`/conversations/${id}?confirm=true`);
    await load();
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Archived Conversations</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-muted-foreground">Loading…</div>
          ) : items.length === 0 ? (
            <div className="text-muted-foreground">No archived conversations.</div>
          ) : (
            <ul className="divide-y divide-border">
              {items.map((c) => (
                <li key={c._id} className="py-3 flex items-center justify-between">
                  <div className="min-w-0">
                    <div className="font-medium">{c.customer_name || c.customer_phone}</div>
                    <div className="text-xs text-muted-foreground">Updated {new Date(c.updated_at as any).toLocaleString()}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    {canRestore && (
                      <Button size="sm" variant="outline" onClick={() => restore(c._id)}>Restore</Button>
                    )}
                    {canPurge && isSuperAdmin(user) && (
                      <Button size="sm" variant="destructive" onClick={() => purge(c._id)}>Purge</Button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}


