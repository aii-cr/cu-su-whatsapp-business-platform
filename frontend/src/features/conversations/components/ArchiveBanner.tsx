"use client";

import { Button } from '@/components/ui/Button';
import { httpClient } from '@/lib/http';

export function ArchiveBanner({ conversationId, isArchived, canArchive, onChanged }: { conversationId: string; isArchived: boolean; canArchive: boolean; onChanged?: () => void }) {
  const toggleArchive = async () => {
    if (!canArchive) return;
    if (isArchived) {
      await httpClient.post(`/conversations/${conversationId}/restore`);
    } else {
      await httpClient.post(`/conversations/${conversationId}/archive`);
    }
    onChanged?.();
  };

  if (!isArchived && !canArchive) return null;

  return (
    <div className="bg-[rgb(var(--surface))] border border-[rgb(var(--border))] text-sm px-3 py-2 rounded flex items-center justify-between">
      <div>
        {isArchived ? 'This conversation is archived.' : 'You can archive this conversation to hide it from active lists.'}
      </div>
      {canArchive && (
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={toggleArchive}>
            {isArchived ? 'Restore' : 'Archive'}
          </Button>
        </div>
      )}
    </div>
  );
}


