import { NextRequest } from 'next/server';
import { getApiUrl } from '@/lib/config';

export async function GET(_req: NextRequest, { params }: { params: { id: string } }) {
  const upstream = `${getApiUrl('')}/conversations/${params.id}/history/export`.replace(/\/$/, '');
  const res = await fetch(upstream, { credentials: 'include' as RequestCredentials });
  const buf = await res.arrayBuffer();
  return new Response(buf, { status: res.status, headers: { 'Content-Type': 'application/pdf' } });
}


