import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { useAuthStore } from './useAuth';
import { useDemoMode } from './useDemoMode';
import { useNotificationStore } from './useNotification';

vi.mock('./useAuth', () => ({
  useAuthStore: vi.fn(),
}));

vi.mock('./useNotification', () => ({
  useNotificationStore: vi.fn(),
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, fallback?: string) => fallback ?? key,
  }),
}));

describe('useDemoMode', () => {
  const notifyInfo = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useNotificationStore).mockReturnValue({ info: notifyInfo } as any);
  });

  it('returns non-read-only state for regular users', () => {
    vi.mocked(useAuthStore).mockReturnValue({ userInfo: { is_demo: false } } as any);

    const { result } = renderHook(() => useDemoMode());

    expect(result.current.isReadOnly).toBe(false);
    expect(result.current.isDemoUser).toBe(false);
  });

  it('blocks actions and notifies for demo users', () => {
    vi.mocked(useAuthStore).mockReturnValue({ userInfo: { is_demo: true } } as any);

    const { result } = renderHook(() => useDemoMode());
    const executed = vi.fn();

    const blocked = result.current.blockIfReadOnly(executed);

    expect(blocked).toBe(true);
    expect(executed).not.toHaveBeenCalled();
    expect(notifyInfo).toHaveBeenCalledWith('Demo Read-Only');
  });

  it('supports an explicit read-only override', () => {
    vi.mocked(useAuthStore).mockReturnValue({ userInfo: { is_demo: false } } as any);

    const { result } = renderHook(() => useDemoMode(true));

    expect(result.current.isReadOnly).toBe(true);
    expect(result.current.isDemoUser).toBe(true);
  });
});
