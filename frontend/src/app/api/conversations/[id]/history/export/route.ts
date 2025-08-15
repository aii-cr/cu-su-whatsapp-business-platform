import { NextRequest } from 'next/server';
import { getApiUrl } from '@/lib/config';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const upstream = `${getApiUrl('')}/conversations/${id}/history/export`.replace(/\/$/, '');
  const res = await fetch(upstream, { credentials: 'include' as RequestCredentials });
  const buf = await res.arrayBuffer();
  return new Response(buf, { status: res.status, headers: { 'Content-Type': 'application/pdf' } });
}


