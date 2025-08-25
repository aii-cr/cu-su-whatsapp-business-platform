/**
 * API functions for Writer Agent operations
 */

import { getApiUrl } from '@/lib/config';

export interface WriterQueryRequest {
  query: string;
  conversation_id?: string;
}

export interface ContextualResponseRequest {
  conversation_id: string;
}

export interface StructuredWriterResponse {
  customer_response: string;
  reason: string;
}

export interface WriterResponse {
  success: boolean;
  response: string;
  metadata: {
    iterations: number;
    helpfulness_score: string;
    processing_time_ms: number;
    node_history: string[];
    conversation_id?: string;
    model_used: string;
  };
  error?: string;
}

export interface WriterAgentResult {
  success: boolean;
  structured_response?: StructuredWriterResponse | null;
  raw_response: string;
  metadata: {
    iterations: number;
    helpfulness_score: string;
    processing_time_ms: number;
    node_history: string[];
    conversation_id?: string;
    model_used: string;
    has_structured_format?: boolean;
  };
  error?: string;
}

/**
 * Generate a response using the Writer Agent
 */
export async function generateWriterResponse(
  request: WriterQueryRequest
): Promise<WriterResponse> {
  const response = await fetch(getApiUrl('ai/writer/generate'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const errorMessage = errorData.error || `Writer Agent error: ${response.statusText}`;
    throw new Error(errorMessage);
  }

  return response.json();
}

/**
 * Generate the best possible response for current conversation context
 */
export async function generateContextualResponse(
  request: ContextualResponseRequest
): Promise<WriterResponse> {
  const response = await fetch(getApiUrl('ai/writer/contextual'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const errorMessage = errorData.error || `Contextual response error: ${response.statusText}`;
    throw new Error(errorMessage);
  }

  return response.json();
}

/**
 * Generate a structured response using the Writer Agent (new format)
 */
export async function generateStructuredWriterResponse(
  request: WriterQueryRequest
): Promise<WriterAgentResult> {
  const response = await fetch(getApiUrl('ai/writer/generate-structured'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const errorMessage = errorData.error || `Structured Writer Agent error: ${response.statusText}`;
    throw new Error(errorMessage);
  }

  return response.json();
}

/**
 * Generate a structured contextual response (new format)
 */
export async function generateStructuredContextualResponse(
  request: ContextualResponseRequest
): Promise<WriterAgentResult> {
  const response = await fetch(getApiUrl('ai/writer/contextual-structured'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const errorMessage = errorData.error || `Structured contextual response error: ${response.statusText}`;
    throw new Error(errorMessage);
  }

  return response.json();
}

/**
 * Check Writer Agent service health
 */
export async function checkWriterHealth(): Promise<any> {
  const response = await fetch(getApiUrl('ai/writer/health'), {
    method: 'GET',
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(`Health check error: ${response.statusText}`);
  }

  return response.json();
}
