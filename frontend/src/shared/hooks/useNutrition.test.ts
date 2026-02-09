import { describe, expect, it, vi, beforeEach } from 'vitest';

import { httpClient } from '../api/http-client';
import type { CreateNutritionLogRequest, NutritionLog, NutritionListResponse, NutritionStats } from '../types/nutrition';

import { useNutritionStore } from './useNutrition';

// Mock httpClient
vi.mock('../api/http-client', () => ({
  httpClient: vi.fn(),
}));

describe('useNutritionStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useNutritionStore.getState().reset();
  });

  const mockLogs: NutritionLog[] = [
    { 
      id: '1', 
      calories: 2000, 
      date: '2024-01-01', 
      user_email: 'test@test.com', 
      protein_grams: 100, 
      carbs_grams: 200, 
      fat_grams: 50, 
      notes: '', 
      source: 'Manual' 
    },
    { 
      id: '2', 
      calories: 1800, 
      date: '2024-01-02', 
      user_email: 'test@test.com', 
      protein_grams: 100, 
      carbs_grams: 200, 
      fat_grams: 50, 
      notes: '', 
      source: 'Manual' 
    },
  ];

  const mockStats: NutritionStats = {
    avg_daily_calories: 2000,
    avg_daily_calories_14_days: 1900,
    avg_protein: 100,
    total_logs: 10,
    today: mockLogs[0]!,
    weekly_adherence: [true, false],
    last_7_days: [],
    last_14_days: []
  };

  it('should have initial state', () => {
    const state = useNutritionStore.getState();
    expect(state.logs).toEqual([]);
    expect(state.stats).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  describe('fetchLogs', () => {
    it('should fetch logs successfully', async () => {
      const mockResponse: NutritionListResponse = {
        logs: mockLogs,
        total: 2,
        page: 1,
        page_size: 10,
        total_pages: 1,
      };
      vi.mocked(httpClient).mockResolvedValue(mockResponse);

      await useNutritionStore.getState().fetchLogs();

      const state = useNutritionStore.getState();
      expect(state.logs).toEqual(mockLogs);
      expect(state.total).toBe(2);
      expect(state.isLoading).toBe(false);
      expect(httpClient).toHaveBeenCalledWith('/nutrition/list?page=1');
    });

    it('should fetch logs with custom page and days', async () => {
      vi.mocked(httpClient).mockResolvedValue({
        logs: [],
        total: 0,
        page: 2,
        page_size: 10,
        total_pages: 0,
      });

      await useNutritionStore.getState().fetchLogs(2, 7);

      expect(httpClient).toHaveBeenCalledWith('/nutrition/list?page=2&days=7');
    });

    it('should handle undefined response', async () => {
      vi.mocked(httpClient).mockResolvedValue(undefined);
      await useNutritionStore.getState().fetchLogs();
      const state = useNutritionStore.getState();
      expect(state.isLoading).toBe(false);
      expect(state.logs).toEqual([]);
    });

    it('should handle fetch logs error', async () => {
      vi.mocked(httpClient).mockRejectedValue(new Error('error'));

      await useNutritionStore.getState().fetchLogs();

      const state = useNutritionStore.getState();
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe('Falha ao carregar histórico nutricional.');
    });
  });

  describe('fetchStats', () => {
    it('should fetch stats successfully', async () => {
      vi.mocked(httpClient).mockResolvedValue(mockStats);
      await useNutritionStore.getState().fetchStats();
      const state = useNutritionStore.getState();
      expect(state.stats).toEqual(mockStats);
      expect(state.isLoading).toBe(false);
    });

    it('should handle undefined stats response', async () => {
      vi.mocked(httpClient).mockResolvedValue(undefined);
      await useNutritionStore.getState().fetchStats();
      const state = useNutritionStore.getState();
      expect(state.stats).toBeNull();
      expect(state.isLoading).toBe(false);
    });

    it('should handle fetch stats error', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      vi.mocked(httpClient).mockRejectedValue(new Error('error'));

      await useNutritionStore.getState().fetchStats();

      const state = useNutritionStore.getState();
      expect(state.isLoading).toBe(false);
      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });
  });

  describe('createLog', () => {
    it('should create log successfully and refresh', async () => {
      // 1. POST create
      vi.mocked(httpClient).mockResolvedValueOnce({ id: '3' });
      // 2. GET list
      vi.mocked(httpClient).mockResolvedValueOnce({ logs: mockLogs, total: 2, page: 1, total_pages: 1, page_size: 10 });
      // 3. GET stats
      vi.mocked(httpClient).mockResolvedValueOnce(mockStats);

      const newLog: CreateNutritionLogRequest = { 
        calories: 2100, 
        date: '2024-01-03', 
        protein_grams: 100,
        carbs_grams: 200,
        fat_grams: 50,
        source: 'Manual'
      };
      await useNutritionStore.getState().createLog(newLog);

      expect(httpClient).toHaveBeenNthCalledWith(1, '/nutrition/log', expect.anything());
      expect(httpClient).toHaveBeenNthCalledWith(2, '/nutrition/list?page=1');
      expect(httpClient).toHaveBeenNthCalledWith(3, '/nutrition/stats');
      
      const state = useNutritionStore.getState();
      expect(state.error).toBeNull();
    });

    it('should handle create log error', async () => {
      vi.mocked(httpClient).mockRejectedValue(new Error('failed'));

      await expect(useNutritionStore.getState().createLog({} as CreateNutritionLogRequest))
        .rejects.toThrow('failed');

      const state = useNutritionStore.getState();
      expect(state.error).toBe('Falha ao salvar registro nutricional.');
      expect(state.isLoading).toBe(false);
    });
  });

  describe('deleteLog', () => {
    it('should delete log and refresh stats', async () => {
      useNutritionStore.setState({ logs: mockLogs, total: 2 });
      
      // 1. DELETE
      vi.mocked(httpClient).mockResolvedValueOnce(undefined);
      // 2. GET stats (refresh)
      vi.mocked(httpClient).mockResolvedValueOnce(mockStats);

      await useNutritionStore.getState().deleteLog('1');

      const state = useNutritionStore.getState();
      expect(state.logs).toHaveLength(1);
      expect(state.logs[0]!.id).toBe('2');
      expect(state.total).toBe(1);
      expect(httpClient).toHaveBeenCalledWith('/nutrition/1', { method: 'DELETE' });
      expect(httpClient).toHaveBeenCalledWith('/nutrition/stats');
    });

    it('should handle delete log error', async () => {
      vi.mocked(httpClient).mockRejectedValue(new Error('failed'));

      await expect(useNutritionStore.getState().deleteLog('1'))
        .rejects.toThrow('failed');

      const state = useNutritionStore.getState();
      expect(state.error).toBe('Falha ao excluir registro.');
      expect(state.isLoading).toBe(false);
    });
  });

  it('should reset state', () => {
    useNutritionStore.setState({ logs: mockLogs, isLoading: true, error: 'error' });
    useNutritionStore.getState().reset();
    const state = useNutritionStore.getState();
    expect(state.logs).toEqual([]);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });
});
