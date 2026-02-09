import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { useNotificationStore } from '../../../shared/hooks/useNotification';
import { bodyApi } from '../api/body-api';

import { useNutritionTab } from './useNutritionTab';

// Mock dependencies
vi.mock('../api/body-api', () => ({
  bodyApi: {
    getNutritionLogs: vi.fn(),
    getNutritionStats: vi.fn(),
    logNutrition: vi.fn(),
    deleteNutritionLog: vi.fn(),
  },
}));

const mockNotify = {
  success: vi.fn(),
  error: vi.fn(),
};

vi.mock('../../../shared/hooks/useNotification', () => ({
  useNotificationStore: vi.fn(),
}));

describe('useNutritionTab hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useNotificationStore as any).mockReturnValue(mockNotify);
  });

  const mockLogs = {
    logs: [{ 
      id: '1', 
      date: '2024-01-01', 
      calories: 2000, 
      source: 'Manual',
      user_email: 'test@test.com',
      protein_grams: 100,
      carbs_grams: 200,
      fat_grams: 50,
      notes: ''
    }],
    total: 1, page: 1, page_size: 10, total_pages: 1,
  };

  const mockStats = { avg_calories: 2000, avg_protein: 150 };

  it('should fetch data on mount', async () => {
    vi.mocked(bodyApi.getNutritionLogs).mockResolvedValue(mockLogs as any);
    vi.mocked(bodyApi.getNutritionStats).mockResolvedValue(mockStats as any);

    const { result } = renderHook(() => useNutritionTab());
    await waitFor(() => { expect(result.current.isLoading).toBe(false); });

    expect(result.current.logs).toHaveLength(1);
    expect(result.current.stats).toEqual(mockStats);
  });

  it('should handle submit success', async () => {
    vi.mocked(bodyApi.getNutritionLogs).mockResolvedValue(mockLogs as any);
    vi.mocked(bodyApi.getNutritionStats).mockResolvedValue(mockStats as any);
    vi.mocked(bodyApi.logNutrition).mockResolvedValue({} as any);

    const { result } = renderHook(() => useNutritionTab());
    await waitFor(() => { expect(result.current.isLoading).toBe(false); });

    await act(async () => {
      // Mocking handleSubmit is tricky with renderHook, 
      // but we can call onSubmit directly if we want to bypass Zod for coverage
      // or we can use the returned handleSubmit which is already wrapped.
      // Better to satisfy Zod if possible.
      result.current.editEntry(mockLogs.logs[0] as any);
      await (result.current.handleSubmit as any)(); 
    });

    expect(bodyApi.logNutrition).toHaveBeenCalled();
    expect(mockNotify.success).toHaveBeenCalledWith('Registro nutricional salvo!');
  });

  it('should handle submit error', async () => {
    vi.mocked(bodyApi.getNutritionLogs).mockResolvedValue(mockLogs as any);
    vi.mocked(bodyApi.getNutritionStats).mockResolvedValue(mockStats as any);
    vi.mocked(bodyApi.logNutrition).mockRejectedValue(new Error('fail'));

    const { result } = renderHook(() => useNutritionTab());
    await waitFor(() => { expect(result.current.isLoading).toBe(false); });

    await act(async () => {
      result.current.editEntry(mockLogs.logs[0] as any);
      await (result.current.handleSubmit as any)();
    });

    expect(mockNotify.error).toHaveBeenCalledWith('Erro ao salvar registro nutricional.');
  });

  it('should handle delete error', async () => {
     vi.mocked(bodyApi.getNutritionLogs).mockResolvedValue(mockLogs as any);
    vi.mocked(bodyApi.getNutritionStats).mockResolvedValue(mockStats as any);
    vi.mocked(bodyApi.deleteNutritionLog).mockRejectedValue(new Error('fail'));

    const { result } = renderHook(() => useNutritionTab());
    await waitFor(() => { expect(result.current.isLoading).toBe(false); });

    await act(async () => {
      await result.current.deleteEntry('1');
    });

    expect(mockNotify.error).toHaveBeenCalledWith('Erro ao remover registro.');
  });
});
