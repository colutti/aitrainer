import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

import { useAuthStore } from './useAuth';
import { useInactivityLogout } from './useInactivityLogout';

describe('useInactivityLogout', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    act(() => {
      useAuthStore.setState({ isAuthenticated: false, userInfo: null, isAdmin: false });
    });
  });


  afterEach(() => {
    vi.useRealTimers();
    act(() => {
      useAuthStore.setState({ isAuthenticated: false, userInfo: null, isAdmin: false });
    });
  });


  it('should not set up listeners when not authenticated', () => {
    const addEventListenerSpy = vi.spyOn(document, 'addEventListener');

    renderHook(() => useInactivityLogout());

    // Verify hook didn't add our specific event listeners
    const callsForOurEvents = addEventListenerSpy.mock.calls.filter(
      ([event]) => ['mousemove', 'mousedown', 'keydown', 'scroll', 'touchstart', 'visibilitychange'].includes(event)
    );
    expect(callsForOurEvents).toHaveLength(0);
    addEventListenerSpy.mockRestore();
  });

  it('should set up listeners when authenticated', () => {
    const addEventListenerSpy = vi.spyOn(document, 'addEventListener');

    act(() => {
      useAuthStore.setState({ isAuthenticated: true });
    });
    renderHook(() => useInactivityLogout());


    // Count calls for our specific listeners only
    const ourListeners = ['mousemove', 'mousedown', 'keydown', 'scroll', 'touchstart', 'visibilitychange'];
    const ourCalls = addEventListenerSpy.mock.calls.filter(([event]) => ourListeners.includes(event));

    // Should attach 6 listeners: 5 activity events + 1 visibilitychange
    expect(ourCalls).toHaveLength(6);
    expect(addEventListenerSpy).toHaveBeenCalledWith('mousemove', expect.any(Function), { passive: true });
    expect(addEventListenerSpy).toHaveBeenCalledWith('mousedown', expect.any(Function), { passive: true });
    expect(addEventListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function), { passive: true });
    expect(addEventListenerSpy).toHaveBeenCalledWith('scroll', expect.any(Function), { passive: true });
    expect(addEventListenerSpy).toHaveBeenCalledWith('touchstart', expect.any(Function), { passive: true });
    expect(addEventListenerSpy).toHaveBeenCalledWith('visibilitychange', expect.any(Function));

    addEventListenerSpy.mockRestore();
  });

  it('should call logout after timeout expires without activity', () => {
    const timeoutMs = 5000;
    const logoutSpy = vi.spyOn(useAuthStore.getState(), 'logout');

    act(() => {
      useAuthStore.setState({ isAuthenticated: true });
    });
    renderHook(() => useInactivityLogout(timeoutMs));


    act(() => {
      vi.advanceTimersByTime(timeoutMs);
    });

    expect(logoutSpy).toHaveBeenCalledTimes(1);
    logoutSpy.mockRestore();
  });

  it('should reset timer on activity event', () => {
    const timeoutMs = 5000;
    const logoutSpy = vi.spyOn(useAuthStore.getState(), 'logout');

    act(() => {
      useAuthStore.setState({ isAuthenticated: true });
    });
    renderHook(() => useInactivityLogout(timeoutMs));


    // Advance time partially
    act(() => {
      vi.advanceTimersByTime(3000);
    });

    // Simulate mousemove activity
    act(() => {
      document.dispatchEvent(new MouseEvent('mousemove'));
    });

    // Advance time by 3000ms more (total 6000ms, but only 3000ms since last activity)
    act(() => {
      vi.advanceTimersByTime(3000);
    });

    expect(logoutSpy).not.toHaveBeenCalled();

    // Advance time by 2000ms more (5000ms since last activity)
    act(() => {
      vi.advanceTimersByTime(2000);
    });

    expect(logoutSpy).toHaveBeenCalledTimes(1);
    logoutSpy.mockRestore();
  });

  it('should throttle activity handler to once per second', () => {
    const timeoutMs = 10000;
    const clearTimeoutSpy = vi.spyOn(global, 'clearTimeout');

    act(() => {
      useAuthStore.setState({ isAuthenticated: true });
    });
    renderHook(() => useInactivityLogout(timeoutMs));


    // Clear the initial clearTimeout call
    clearTimeoutSpy.mockClear();

    // Fire multiple mousemove events rapidly
    act(() => {
      for (let i = 0; i < 10; i++) {
        document.dispatchEvent(new MouseEvent('mousemove'));
        vi.advanceTimersByTime(50);
      }
    });

    // Should only reset timer once (first event triggers reset, rest are throttled)
    expect(clearTimeoutSpy.mock.calls.length).toBeLessThanOrEqual(1);
    clearTimeoutSpy.mockRestore();
  });

  it('should handle visibility change - logout if timeout already elapsed', () => {
    const timeoutMs = 5000;
    const logoutSpy = vi.spyOn(useAuthStore.getState(), 'logout');

    act(() => {
      useAuthStore.setState({ isAuthenticated: true });
    });
    renderHook(() => useInactivityLogout(timeoutMs));


    // Simulate time passing while tab is hidden (6000ms > 5000ms timeout)
    act(() => {
      vi.advanceTimersByTime(6000);
    });

    // Simulate tab becoming visible
    act(() => {
      Object.defineProperty(document, 'visibilityState', {
        value: 'visible',
        writable: true,
      });
      document.dispatchEvent(new Event('visibilitychange'));
    });

    expect(logoutSpy).toHaveBeenCalled();
    logoutSpy.mockRestore();
  });

  it('should handle visibility change - recalculate if timeout not yet elapsed', () => {
    const timeoutMs = 10000;
    const logoutSpy = vi.spyOn(useAuthStore.getState(), 'logout');

    act(() => {
      useAuthStore.setState({ isAuthenticated: true });
    });
    renderHook(() => useInactivityLogout(timeoutMs));


    // Advance time by 3000ms
    act(() => {
      vi.advanceTimersByTime(3000);
    });

    // Simulate tab becoming visible (still have 7000ms remaining)
    act(() => {
      Object.defineProperty(document, 'visibilityState', {
        value: 'visible',
        writable: true,
      });
      document.dispatchEvent(new Event('visibilitychange'));
    });

    // Advance by 6999ms - should NOT logout yet
    act(() => {
      vi.advanceTimersByTime(6999);
    });
    expect(logoutSpy).not.toHaveBeenCalled();

    // Advance by 1ms more - should logout
    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(logoutSpy).toHaveBeenCalledTimes(1);
    logoutSpy.mockRestore();
  });

  it('should clean up on unmount', () => {
    const removeEventListenerSpy = vi.spyOn(document, 'removeEventListener');
    const clearTimeoutSpy = vi.spyOn(global, 'clearTimeout');

    act(() => {
      useAuthStore.setState({ isAuthenticated: true });
    });
    const { unmount } = renderHook(() => useInactivityLogout());


    removeEventListenerSpy.mockClear();
    clearTimeoutSpy.mockClear();

    act(() => {
      unmount();
    });

    // Should remove our 6 listeners (5 activity + 1 visibility change)
    const ourListeners = ['mousemove', 'mousedown', 'keydown', 'scroll', 'touchstart', 'visibilitychange'];
    const ourRemovalCalls = removeEventListenerSpy.mock.calls.filter(([event]) => ourListeners.includes(event));
    expect(ourRemovalCalls.length).toBeGreaterThanOrEqual(6);
    // Should clear the timeout
    expect(clearTimeoutSpy).toHaveBeenCalled();

    removeEventListenerSpy.mockRestore();
    clearTimeoutSpy.mockRestore();
  });
});
