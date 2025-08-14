import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Check for protected routes
  const isProtected = request.nextUrl.pathname.startsWith('/conversations');
  const hasSession = request.cookies.get('session_token')?.value;

  if (isProtected && !hasSession) {
    const url = new URL('/login', request.url);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/conversations/:path*'],
};


