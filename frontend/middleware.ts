import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Example: Basic auth gating for protected routes under /conversations
  // In a real app, read a session cookie set by your backend and validate it.
  const isProtected = request.nextUrl.pathname.startsWith('/conversations');
  const hasSession = request.cookies.get('session')?.value;

  if (isProtected && !hasSession) {
    const url = new URL('/login', request.url);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/conversations/:path*'],
};


