import { useEffect, useRef, useCallback } from 'react';

import { useAuthStore } from './useAuth';

const INACTIVITY_TIMEOUT_MS = 50 * 60 * 1000; // 50 minutes

const ACTIVITY_EVENTS: string[] = [
  'mousemove',
  'mousedown',
  'keydown',
  'scroll',
  'touchstart',
];

/**
 * Hook that automatically logs the user out after a period of inactivity.
 *
 * Monitors user activity events (mouse, keyboard, scroll, touch) and
 * resets a countdown timer on each activity. When the timer expires
 * without any activity, calls logout() from the auth store.
 *
 * Also handles tab visibility changes: when the tab becomes visible
 * again, it checks whether the inactivity period has already elapsed
 * while the tab was hidden.
 *
 * @param timeoutMs - Inactivity timeout in milliseconds (default: 50 minutes)
 */
export function useInactivityLogout(timeoutMs: number = INACTIVITY_TIMEOUT_MS): void {
  const logout = useAuthStore((state) => state.logout);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastActivityRef = useRef<number>(0);

  const handleLogout = useCallback(() => {
    logout();
  }, [logout]);

  const resetTimer = useCallback(() => {
    lastActivityRef.current = Date.now();

    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
    }

    timerRef.current = setTimeout(handleLogout, timeoutMs);
  }, [handleLogout, timeoutMs]);

  // Throttled activity handler - at most one reset per second
  const lastResetRef = useRef<number>(0);
  const handleActivity = useCallback(() => {
    const now = Date.now();
    if (now - lastResetRef.current < 1000) {
      return; // Throttle: skip if less than 1 second since last reset
    }
    lastResetRef.current = now;
    resetTimer();
  }, [resetTimer]);

  // Handle tab visibility changes
  const handleVisibilityChange = useCallback(() => {
    if (document.visibilityState === 'visible') {
      const elapsed = Date.now() - lastActivityRef.current;
      if (elapsed >= timeoutMs) {
        handleLogout();
      } else {
        // Reset timer with remaining time
        if (timerRef.current !== null) {
          clearTimeout(timerRef.current);
        }
        timerRef.current = setTimeout(handleLogout, timeoutMs - elapsed);
      }
    }
  }, [handleLogout, timeoutMs]);

  useEffect(() => {
    if (!isAuthenticated) {
      return; // Don't set up listeners if not logged in
    }

    // Start the initial timer
    resetTimer();

    // Attach activity listeners (passive for performance)
    for (const event of ACTIVITY_EVENTS) {
      document.addEventListener(event, handleActivity, { passive: true });
    }

    // Attach visibility change listener
    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Cleanup
    return () => {
      if (timerRef.current !== null) {
        clearTimeout(timerRef.current);
      }
      for (const event of ACTIVITY_EVENTS) {
        document.removeEventListener(event, handleActivity);
      }
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [isAuthenticated, resetTimer, handleActivity, handleVisibilityChange]);
}
