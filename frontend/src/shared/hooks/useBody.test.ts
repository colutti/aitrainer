import { describe, expect, it, vi, beforeEach } from 'vitest';

import { httpClient } from '../api/http-client';
import type { WeightLog, BodyCompositionStats } from '../types/body';

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

  const mockLogs: WeightLog[] = [
    { date: '2024-01-01', weight_kg: 80, user_email: 'test@example.com' },
    { date: '2024-01-02', weight_kg: 79, user_email: 'test@example.com' },
  ];

  const mockStats: BodyCompositionStats = {
    latest: { weight_kg: 80, date: '2024-01-01', user_email: 'test@example.com' },
    weight_trend: [],
    fat_trend: [],
    muscle_trend: [],
  };

  describe('fetchLogs', () => {
    it('should fetch logs successfully (paginated response)', async () => {
      vi.mocked(httpClient).mockResolvedValue({ logs: mockLogs, total: 2 });
      
      await useBodyStore.getState().fetchLogs();
      
      const state = useBodyStore.getState();
      expect(state.logs).toEqual(mockLogs);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
      expect(httpClient).toHaveBeenCalledWith('/weight?limit=30');
    });

    it('should handle fetch logs error', async () => {
      vi.mocked(httpClient).mockRejectedValue(new Error('Network error'));
      
      await useBodyStore.getState().fetchLogs();
      
      const state = useBodyStore.getState();
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe('Falha ao carregar histórico de peso.');
    });
  });

  describe('fetchStats', () => {
    it('should fetch stats successfully', async () => {
      vi.mocked(httpClient).mockResolvedValue(mockStats);
      
      await useBodyStore.getState().fetchStats();
      
      const state = useBodyStore.getState();
      expect(state.stats).toEqual(mockStats);
      expect(state.isLoading).toBe(false);
    });

    it('should handle fetch stats error', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      vi.mocked(httpClient).mockRejectedValue(new Error('Network error'));
      
      await useBodyStore.getState().fetchStats();
      
      const state = useBodyStore.getState();
      expect(state.isLoading).toBe(false);
      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });
  });

  describe('logWeight', () => {
    it('should log weight successfully and refresh data', async () => {
      vi.mocked(httpClient).mockResolvedValue({}); // log response
      // Mock subsequent fetch calls
      vi.mocked(httpClient)
        .mockResolvedValueOnce({}) // logWeight
        .mockResolvedValueOnce({ logs: mockLogs }) // fetchLogs
        .mockResolvedValueOnce(mockStats); // fetchStats

      await useBodyStore.getState().logWeight({ weight_kg: 81, date: '2024-01-03' });
      
      expect(httpClient).toHaveBeenCalledWith('/weight', expect.objectContaining({
        method: 'POST',
        body: expect.stringContaining('"weight_kg":81')
      }));
    });

    it('should handle log weight error', async () => {
      vi.mocked(httpClient).mockRejectedValue(new Error('Failed'));
      
      await expect(useBodyStore.getState().logWeight({ weight_kg: 81 }))
        .rejects.toThrow('Failed');
        
      const state = useBodyStore.getState();
      expect(state.error).toBe('Falha ao registrar peso.');
      expect(state.isLoading).toBe(false);
    });
  });

  describe('deleteLog', () => {
    it('should delete log successfully', async () => {
      useBodyStore.setState({ logs: mockLogs });
      vi.mocked(httpClient).mockResolvedValue({});
      
      await useBodyStore.getState().deleteLog('2024-01-01');
      
      const state = useBodyStore.getState();
      expect(state.logs).toHaveLength(1);
      expect(state.logs[0]!.date).toBe('2024-01-02');
      expect(httpClient).toHaveBeenCalledWith('/weight/2024-01-01', { method: 'DELETE' });
    });

    it('should handle delete log error', async () => {
      vi.mocked(httpClient).mockRejectedValue(new Error('Failed'));
      
      await expect(useBodyStore.getState().deleteLog('2024-01-01'))
        .rejects.toThrow('Failed');
        
      const state = useBodyStore.getState();
      expect(state.error).toBe('Falha ao excluir registro.');
      expect(state.isLoading).toBe(false);
    });
  });

  describe('reset', () => {
    it('should reset state', () => {
      useBodyStore.setState({ 
        logs: mockLogs, 
        stats: mockStats, 
        isLoading: true, 
        error: 'Error' 
      });
      
      useBodyStore.getState().reset();
      
      const state = useBodyStore.getState();
      expect(state.logs).toEqual([]);
      expect(state.stats).toBeNull();
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
    });
  });
});
