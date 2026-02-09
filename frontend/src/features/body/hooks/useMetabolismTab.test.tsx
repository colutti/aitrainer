import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { bodyApi } from '../api/body-api';

import { useMetabolismTab } from './useMetabolismTab';

// Mock dependencies
vi.mock('../api/body-api', () => ({
  bodyApi: {
    getMetabolismSummary: vi.fn(),
  },
}));

const mockNotify = {
  success: vi.fn(),
  error: vi.fn(),
};

vi.mock('../../../shared/hooks/useNotification', () => ({
  useNotificationStore: () => mockNotify,
}));

describe('useMetabolismTab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockStats = {
    bmr: 1800,
    tdee: 2500,
    weekly_trend: [],
  };

  it('should load initial data', async () => {
    vi.mocked(bodyApi.getMetabolismSummary).mockResolvedValue(mockStats as unknown as Awaited<ReturnType<typeof bodyApi.getMetabolismSummary>>);

    const { result } = renderHook(() => useMetabolismTab());

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.stats).toEqual(mockStats);
    expect(bodyApi.getMetabolismSummary).toHaveBeenCalledWith(3); // Default weeks
  });

  it('should update weeks and reload', async () => {
    vi.mocked(bodyApi.getMetabolismSummary).mockResolvedValue(mockStats as unknown as Awaited<ReturnType<typeof bodyApi.getMetabolismSummary>>);

    const { result } = renderHook(() => useMetabolismTab());
    await waitFor(() => { expect(result.current.isLoading).toBe(false); });

    act(() => {
      result.current.setWeeks(4);
    });

    expect(result.current.weeks).toBe(4);
    // useEffect should trigger loadData
    expect(bodyApi.getMetabolismSummary).toHaveBeenCalledWith(4);
  });
  
  it('should handle load error', async () => {
    vi.mocked(bodyApi.getMetabolismSummary).mockRejectedValue(new Error('API Error'));

    const { result } = renderHook(() => useMetabolismTab());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockNotify.error).toHaveBeenCalledWith('Erro ao carregar dados metabólicos.');
  });
});
