import { useAuth } from '../store/auth';

const BASE = '/api/v1';

export class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, message: string, body: unknown) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  query?: Record<string, string | number | undefined>;
  raw?: boolean;
}

function buildUrl(path: string, query?: RequestOptions['query']): string {
  const url = new URL(BASE + path, window.location.origin);
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      if (v !== undefined) url.searchParams.set(k, String(v));
    }
  }
  return url.pathname + url.search;
}

export async function api<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, query, raw } = opts;
  const apiKey = useAuth.getState().apiKey;
  const headers: Record<string, string> = {
    Accept: 'application/json',
  };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (apiKey) headers['X-Api-Key'] = apiKey;

  const res = await fetch(buildUrl(path, query), {
    method,
    headers,
    credentials: 'include',
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401 && !path.startsWith('/login') && !path.startsWith('/ping')) {
    useAuth.getState().clear();
    if (window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
    throw new ApiError(401, 'Unauthorized', null);
  }

  if (!res.ok) {
    let parsed: unknown = null;
    try { parsed = await res.json(); } catch { /* ignore */ }
    const msg =
      parsed && typeof parsed === 'object' && 'message' in parsed
        ? String((parsed as { message: unknown }).message)
        : `HTTP ${res.status}`;
    throw new ApiError(res.status, msg, parsed);
  }

  if (raw) return res as unknown as T;
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
