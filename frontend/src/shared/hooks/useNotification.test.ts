import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useNotificationStore } from './useNotification';

describe('useNotification', () => {
  beforeEach(() => {
    // Reset store state - must be done in act
    act(() => {
      useNotificationStore.setState({ notifications: [] });
    });
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Initial State', () => {
    it('should have empty notifications array', () => {
      const { result } = renderHook(() => useNotificationStore());

      expect(result.current.notifications).toEqual([]);
    });
  });

  describe('show', () => {
    it('should add notification with unique id', () => {
      const { result } = renderHook(() => useNotificationStore());

      act(() => {
        result.current.show('Test message', 'info');
      });

      expect(result.current.notifications).toHaveLength(1);
      expect(result.current.notifications[0]).toMatchObject({
        message: 'Test message',
        type: 'info',
      });
      expect(result.current.notifications[0]?.id).toBeDefined();
    });

    it('should add multiple notifications', () => {
      const { result } = renderHook(() => useNotificationStore());

      act(() => {
        result.current.show('Message 1', 'info');
        result.current.show('Message 2', 'success');
        result.current.show('Message 3', 'error');
      });

      expect(result.current.notifications).toHaveLength(3);
      expect(result.current.notifications[0]?.message).toBe('Message 1');
      expect(result.current.notifications[1]?.message).toBe('Message 2');
      expect(result.current.notifications[2]?.message).toBe('Message 3');
    });

    it('should auto-remove notification after duration', () => {
      const { result } = renderHook(() => useNotificationStore());

      act(() => {
        result.current.show('Auto remove', 'info', 3000);
      });

      expect(result.current.notifications).toHaveLength(1);

      act(() => {
        vi.advanceTimersByTime(3000);
      });

      expect(result.current.notifications).toHaveLength(0);
    });

    it('should use default duration of 5000ms', () => {
      const { result } = renderHook(() => useNotificationStore());

      act(() => {
        result.current.show('Default duration', 'info');
      });

      expect(result.current.notifications).toHaveLength(1);

      act(() => {
        vi.advanceTimersByTime(4999);
      });

      expect(result.current.notifications).toHaveLength(1);

      act(() => {
        vi.advanceTimersByTime(1);
      });

      expect(result.current.notifications).toHaveLength(0);
    });
  });

  describe('Helper methods', () => {
    it('success should add success notification', () => {
      const { result } = renderHook(() => useNotificationStore());

      act(() => {
        result.current.success('Success message');
      });

      expect(result.current.notifications[0]).toMatchObject({
        message: 'Success message',
        type: 'success',
      });
    });

    it('error should add error notification', () => {
      const { result } = renderHook(() => useNotificationStore());

      act(() => {
        result.current.error('Error message');
      });

      expect(result.current.notifications[0]).toMatchObject({
        message: 'Error message',
        type: 'error',
      });
    });

    it('info should add info notification', () => {
      const { result } = renderHook(() => useNotificationStore());

      act(() => {
        result.current.info('Info message');
      });

      expect(result.current.notifications[0]).toMatchObject({
        message: 'Info message',
        type: 'info',
      });
    });
  });

  describe('remove', () => {
    it('should remove notification by id', () => {
      // Use real timers for this test since we're testing manual removal
      vi.useRealTimers();

      const { result } = renderHook(() => useNotificationStore());

      act(() => {
        result.current.show('Test message', 'info', 999999); // Long duration to prevent auto-dismiss
      });

      const notificationId = result.current.notifications[0]?.id;
      expect(result.current.notifications).toHaveLength(1);
      expect(notificationId).toBeDefined();

      if (!notificationId) {
        throw new Error('Notification ID should be defined');
      }

      act(() => {
        result.current.remove(notificationId);
      });

      expect(result.current.notifications).toHaveLength(0);

      // Restore fake timers for other tests
      vi.useFakeTimers();
    });

    it('should not error when removing non-existent id', () => {
      const { result } = renderHook(() => useNotificationStore());

      act(() => {
        result.current.remove('non-existent-id');
      });

      expect(result.current.notifications).toHaveLength(0);
    });
  });

  describe('clear', () => {
    it('should remove all notifications', () => {
      const { result } = renderHook(() => useNotificationStore());

      act(() => {
        result.current.show('Message 1', 'info');
        result.current.show('Message 2', 'success');
        result.current.show('Message 3', 'error');
      });

      expect(result.current.notifications).toHaveLength(3);

      act(() => {
        result.current.clear();
      });

      expect(result.current.notifications).toHaveLength(0);
    });
  });
});
