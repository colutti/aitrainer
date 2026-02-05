import { describe, expect, it, vi, beforeEach } from 'vitest';

import { httpClient } from '../api/http-client';
import { useBodyStore } from './useBody';

// Mock httpClient
vi.mock('../api/http-client', () => ({
  httpClient: vi.fn(),
}));

describe('useBodyStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useBodyStore.getState().reset();
  });

  it('should have initial state', () => {
    const state = useBodyStore.getState();
    expect(state.logs).toEqual([]);
    expect(state.stats).toBeNull();
    expect(state.isLoading).toBe(false);
  });

  it('should fetch stats successfully', async () => {
    const mockStats = {
      latest: { weight_kg: 80, date: '2024-01-01' },
      weight_trend: [],
      fat_trend: [],
      muscle_trend: [],
    };

    vi.mocked(httpClient).mockResolvedValue(mockStats);

    await useBodyStore.getState().fetchStats();

    const state = useBodyStore.getState();
    expect(state.stats).toEqual(mockStats);
    expect(state.isLoading).toBe(false);
    expect(httpClient).toHaveBeenCalledWith('/weight/stats');
  });

  it('should handle delete log', async () => {
    const initialLogs = [
      { date: '2024-01-01', weight_kg: 80 } as any,
      { date: '2024-01-02', weight_kg: 79 } as any,
    ];
    
    useBodyStore.setState({ logs: initialLogs });
    vi.mocked(httpClient).mockResolvedValue({ message: 'Deleted' });

    await useBodyStore.getState().deleteLog('2024-01-01');

    const state = useBodyStore.getState();
    expect(state.logs).toHaveLength(1);
    expect(state.logs[0].date).toBe('2024-01-02');
    expect(httpClient).toHaveBeenCalledWith('/weight/2024-01-01', { method: 'DELETE' });
  });
});
