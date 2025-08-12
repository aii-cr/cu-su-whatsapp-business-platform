import { NextRequest } from 'next/server';
import { getApiUrl } from '@/lib/config';

export async function GET(_req: NextRequest, { params }: { params: { id: string } }) {
  const upstream = `${getApiUrl('')}/conversations/${params.id}/history`.replace(/\/$/, '');
  const res = await fetch(upstream, { credentials: 'include' as RequestCredentials, headers: { 'Content-Type': 'application/json' } });
  const body = await res.text();
  return new Response(body, { status: res.status, headers: { 'Content-Type': res.headers.get('content-type') || 'application/json' } });
}


