/**
 * HTTP client for API requests
 * Automatically handles authentication, error responses, and JSON parsing
 */

import { getRuntimeConfigValue } from '../config/runtime-config';

export const getApiBaseUrl = (): string =>
  getRuntimeConfigValue('VITE_API_URL') ??
  (import.meta.env.VITE_API_URL as string | undefined) ??
  '/api';

export const API_BASE_URL = getApiBaseUrl();
const AUTH_TOKEN_KEY = 'auth_token';

interface RequestConfig extends RequestInit {
  headers?: Record<string, string>;
  _isRetry?: boolean;
  cacheBust?: boolean;
}

interface ErrorResponse {
  detail?: string;
}

/**
 * Makes an authenticated HTTP request to the API
 *
 * @param endpoint - API endpoint (without /api prefix)
 * @param config - Fetch request configuration
 * @returns Parsed JSON response
 * @throws Error with message from API or generic error message
 *
 * @example
 * ```ts
 * const user = await httpClient<UserProfile>('/users/me');
 * await httpClient('/auth/logout', { method: 'POST' });
 * ```
 */
export async function httpClient<T = unknown>(
  endpoint: string,
  config: RequestConfig = {}
): Promise<T | undefined> {
  const token = localStorage.getItem(AUTH_TOKEN_KEY);

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0',
    ...config.headers,
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let url = `${getApiBaseUrl()}${endpoint}`;
  
  // Optional cache busting for selected GET requests.
  if (config.cacheBust && (!config.method || config.method.toUpperCase() === 'GET')) {
    const separator = url.includes('?') ? '&' : '?';
    url = `${url}${separator}_t=${Date.now().toString()}`;
  }

  try {
    const response = await fetch(url, {
      ...config,
      headers,
    });

    // Handle 401 Unauthorized — attempt silent token refresh, then retry once
    if (response.status === 401) {
      const { useAuthStore } = await import('../hooks/useAuth');

      // Attempt refresh (only if this isn't already a retry)
      if (!config._isRetry) {
        const refreshed = await useAuthStore.getState().refreshToken();
        if (refreshed) {
          // Retry original request with the new token
          return await httpClient<T>(endpoint, { ...config, _isRetry: true });
        }
      }

      // Refresh failed or this is already a retry — logout
      useAuthStore.getState().logout();

      const error = (await response.json().catch(() => ({
        detail: 'Unauthorized',
      }))) as ErrorResponse;
      throw new Error(error.detail ?? 'Unauthorized');
    }

    // Handle other error responses
    if (!response.ok) {
      const error = (await response.json().catch(() => ({
        detail: `HTTP error ${response.status.toString()}`,
      }))) as ErrorResponse;
      throw new Error(error.detail ?? `HTTP error ${response.status.toString()}`);
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return undefined;
    }

    // Parse and return JSON response
    try {
      return (await response.json()) as T;
    } catch {
      // If JSON parsing fails (e.g., empty body), return undefined
      return undefined;
    }
  } catch (error) {
    // Re-throw if it's already our formatted error
    if (error instanceof Error) {
      throw error;
    }
    // Handle network errors
    throw new Error('Network error');
  }
}
