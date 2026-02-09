import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { useNotificationStore } from '../../../shared/hooks/useNotification';
import { bodyApi } from '../api/body-api';

import { useWeightTab } from './useWeightTab';

// Mock dependencies
vi.mock('../api/body-api', () => ({
  bodyApi: {
    getBodyCompositionStats: vi.fn(),
    getWeightHistory: vi.fn(),
    logWeight: vi.fn(),
    deleteWeight: vi.fn(),
  },
}));

const mockNotify = {
  success: vi.fn(),
  error: vi.fn(),
};

vi.mock('../../../shared/hooks/useNotification', () => ({
  useNotificationStore: vi.fn(),
}));

describe('useWeightTab hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useNotificationStore as any).mockReturnValue(mockNotify);
  });

  const mockHistory = {
    logs: [{ date: '2024-01-01', weight_kg: 80, body_fat_pct: 15, muscle_mass_pct: 40 }],
    total: 1, page: 1, total_pages: 1,
  };

  const mockStats = { current_weight: 80, target_weight: 75 };

  it('should handle submit success', async () => {
    vi.mocked(bodyApi.getBodyCompositionStats).mockResolvedValue(mockStats as any);
    vi.mocked(bodyApi.getWeightHistory).mockResolvedValue(mockHistory as any);
    vi.mocked(bodyApi.logWeight).mockResolvedValue({} as any);

    const { result } = renderHook(() => useWeightTab());
    await waitFor(() => { expect(result.current.isLoading).toBe(false); });

    await act(async () => {
      result.current.editEntry(mockHistory.logs[0] as any);
      await (result.current.handleSubmit as any)();
    });

    expect(bodyApi.logWeight).toHaveBeenCalled();
    expect(mockNotify.success).toHaveBeenCalledWith('Registro de peso salvo!');
  });

  it('should handle submit error', async () => {
    vi.mocked(bodyApi.getBodyCompositionStats).mockResolvedValue(mockStats as any);
    vi.mocked(bodyApi.getWeightHistory).mockResolvedValue(mockHistory as any);
    vi.mocked(bodyApi.logWeight).mockRejectedValue(new Error('fail'));

    const { result } = renderHook(() => useWeightTab());
    await waitFor(() => { expect(result.current.isLoading).toBe(false); });

    await act(async () => {
      result.current.editEntry(mockHistory.logs[0] as any);
      await (result.current.handleSubmit as any)();
    });

    expect(mockNotify.error).toHaveBeenCalledWith('Erro ao salvar registro de peso.');
  });
});
