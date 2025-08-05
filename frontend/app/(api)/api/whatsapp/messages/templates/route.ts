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
    
    // Prepare headers for FastAPI backend
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    // Add session cookie if available
    if (cookieHeader) {
      headers['Cookie'] = cookieHeader;
    }
    
    // Proxy request to FastAPI backend
    const response = await fetch(`${API_BASE_URL}/api/v1/messages/templates`, {
      method: 'GET',
      headers,
    });

    const data = await response.json();

    if (!response.ok) {
      console.error('Templates API error:', data);
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