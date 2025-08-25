export async function bffRequest<T = unknown>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path.startsWith('/') ? path : '/' + path}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
    ...init,
  });
  const ct = res.headers.get('content-type') || '';
  const isJson = ct.includes('application/json');
  if (!res.ok) {
    const data = isJson ? await res.json().catch(() => ({})) : {};
    throw { statusCode: res.status, ...data };
  }
  return (isJson ? await res.json() : (undefined as unknown)) as T;
}

export const bff = {
  get: <T>(path: string) => bffRequest<T>(path, { method: 'GET' }),
  post: <T>(path: string, body?: unknown) => bffRequest<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) => bffRequest<T>(path, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => bffRequest<T>(path, { method: 'DELETE' }),
};


