// Admin API HTTP client
// Points to the separate admin backend

const VITE_ADMIN_API_URL = import.meta.env.VITE_ADMIN_API_URL as string | undefined;
const VITE_ADMIN_SECRET_KEY = import.meta.env.VITE_ADMIN_SECRET_KEY as string | undefined;

export const API_BASE_URL: string = VITE_ADMIN_API_URL ?? 'http://localhost:8001';
const ADMIN_SECRET_KEY: string = VITE_ADMIN_SECRET_KEY ?? '';

export interface HttpClientOptions extends RequestInit {
  body?: string;
}

/**
 * HTTP client for admin API calls
 * Automatically adds JWT token and X-Admin-Key headers
 */
export async function httpClient<T = unknown>(
  path: string,
  options: HttpClientOptions = {},
): Promise<T> {
  const { getAdminToken } = await import('../hooks/useAdminAuth');

  const token = getAdminToken();

  const headers = new Headers(options.headers ?? {});
  headers.set('Content-Type', 'application/json');

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  if (ADMIN_SECRET_KEY) {
    headers.set('X-Admin-Key', ADMIN_SECRET_KEY);
  }

  const url = `${API_BASE_URL}${path}`;

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      const error = (await response.json()) as { detail?: string };
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    throw new Error(`HTTP ${response.status}`);
  }

  if (response.status === 204) {
    return null as unknown as T;
  }

  const contentType = response.headers.get('content-type');
  if (contentType?.includes('application/json')) {
    return (await response.json()) as T;
  }

  throw new Error(`Unexpected response content type: ${contentType}`);
}
