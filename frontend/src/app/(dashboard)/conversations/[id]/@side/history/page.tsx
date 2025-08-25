"use client";

import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { httpClient } from '@/lib/http';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { formatMessageTime } from '@/lib/timezone';

export default function HistoryPanel() {
  const params = useParams();
  const id = params.id as string;

  const { data, isLoading } = useQuery({
    queryKey: ['conversation', id, 'history'],
    queryFn: async () => await httpClient.get<{ items: Array<{ type: string; ts_utc: string; payload: any }> }>(`/conversations/${id}/history`),
  });

  const exportPdf = async () => {
    const res = await fetch(`${(httpClient as any).baseUrl}/conversations/${id}/history/export`, {
      credentials: 'include',
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conversation-${id}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Card>
      <CardHeader className="flex items-center justify-between">
        <CardTitle>History</CardTitle>
        <Button size="sm" onClick={exportPdf}>Export PDF</Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="text-sm text-muted-foreground">Loading...</div>
        ) : (
          <ul className="space-y-3">
            {data?.items?.map((it, idx) => (
              <li key={idx} className="text-sm">
                <div className="text-muted-foreground text-xs">{formatMessageTime(it.ts_utc)}</div>
                <div className="font-medium capitalize">{it.type.replaceAll('_',' ')}</div>
                {it.payload?.text && <div className="text-foreground">{it.payload.text}</div>}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}


