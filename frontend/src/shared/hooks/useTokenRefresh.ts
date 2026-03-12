import { useEffect, useRef } from 'react';

import { isTokenExpiringSoon } from '../utils/jwt';

import { useAuthStore } from './useAuth';

const CHECK_INTERVAL_MS = 60 * 1000; // Check every minute
const REFRESH_THRESHOLD_MS = 5 * 60 * 1000; // Refresh when < 5 minutes remain

/**
 * Proactively refreshes the JWT token before it expires.
 *
 * Checks token expiry every minute. When the token has less than
 * 5 minutes remaining, silently fetches a new token from /user/refresh.
 * This prevents active users from being disconnected due to token expiry.
 *
 * Works in conjunction with useInactivityLogout: inactive users are
 * logged out after 50 minutes, while active users never expire.
 */
export function useTokenRefresh(): void {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const refreshToken = useAuthStore((state) => state.refreshToken);
  const getToken = useAuthStore((state) => state.getToken);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!isAuthenticated) return;

    intervalRef.current = setInterval(() => {
      const token = getToken();
      if (token && isTokenExpiringSoon(token, REFRESH_THRESHOLD_MS)) {
        void refreshToken();
      }
    }, CHECK_INTERVAL_MS);

    return () => {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isAuthenticated, refreshToken, getToken]);
}
