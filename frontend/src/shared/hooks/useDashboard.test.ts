import { describe, expect, it, vi, beforeEach } from 'vitest';

import { httpClient } from '../api/http-client';

import { useDashboardStore } from './useDashboard';

// Mock httpClient
vi.mock('../api/http-client', () => ({
  httpClient: vi.fn(),
}));

describe('useDashboardStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useDashboardStore.getState().reset();
  });

  it('should have initial state', () => {
    const state = useDashboardStore.getState();
    expect(state.data).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('should fetch dashboard data successfully', async () => {
    const mockData = {
      stats: {
        weight: { current: 80, difference: -2, trend: 'down' },
        calories: { consumed: 2000, target: 2500, percent: 80 },
        workouts: { completed: 3, target: 5 },
        water: { consumed: 2000, target: 3000 },
      },
      recentActivities: [],
    };

    vi.mocked(httpClient).mockResolvedValue(mockData);

    await useDashboardStore.getState().fetchData();

    const state = useDashboardStore.getState();
    expect(state.data).toEqual(mockData);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
    expect(httpClient).toHaveBeenCalledWith('/dashboard');
  });

  it('should handle fetch errors', async () => {
    vi.mocked(httpClient).mockRejectedValue(new Error('Failed to fetch'));
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation((_err) => { /* suppress */ });

    await useDashboardStore.getState().fetchData();

    const state = useDashboardStore.getState();
    expect(state.data).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBe('Failed to fetch dashboard data');
    consoleSpy.mockRestore();
  });
});
