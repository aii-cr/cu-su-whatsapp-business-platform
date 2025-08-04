/**
 * BFF API route for getting WhatsApp message templates.
 * Proxies requests to the FastAPI backend.
 */

import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  try {
    // Get session cookie from request
    const cookieHeader = request.headers.get('cookie');
    
    // Proxy request to FastAPI backend
    const response = await fetch(`${API_BASE_URL}/api/whatsapp/chat/messages/templates`, {
      method: 'GET',
      headers: {
        'Cookie': cookieHeader || '',
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Error getting templates:', error);
    return NextResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    );
  }
}