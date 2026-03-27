import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useNotificationStore } from '../../../shared/hooks/useNotification';
import { bodyApi } from '../api/body-api';

import { useNutritionTab } from './useNutritionTab';

const mockNotifications = {
  success: vi.fn(),
  error: vi.fn(),
  info: vi.fn(),
  show: vi.fn(),
  remove: vi.fn(),
  clear: vi.fn(),
  notifications: [],
};

vi.mock('../api/body-api', () => ({
  bodyApi: {
    getNutritionLogs: vi.fn(),
    getNutritionStats: vi.fn(),
    logNutrition: vi.fn(),
    deleteNutritionLog: vi.fn(),
  },
}));

vi.mock('../../../shared/hooks/useNotification', () => ({
  useNotificationStore: vi.fn(() => mockNotifications),
}));

describe('useNutritionTab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal('scrollTo', vi.fn());
    vi.mocked(useNotificationStore).mockReturnValue(mockNotifications);
    vi.mocked(bodyApi.getNutritionStats).mockResolvedValue({
      avg_calories: 2200,
    } as never);
    vi.mocked(bodyApi.getNutritionLogs).mockImplementation(
      async (page = 1, _pageSize = 10, _days) =>
        ({
          logs: [],
          page,
          total_pages: 3,
        }) as never
    );
  });

  it('loads stats and logs on mount', async () => {
    const { result } = renderHook(() => useNutritionTab());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(bodyApi.getNutritionStats).toHaveBeenCalledOnce();
    expect(bodyApi.getNutritionLogs).toHaveBeenCalledWith(1, 10, undefined);
  });

  it('changes filter and reloads page 1', async () => {
    const { result } = renderHook(() => useNutritionTab());

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      result.current.setFilter(30);
    });

    expect(bodyApi.getNutritionLogs).toHaveBeenLastCalledWith(1, 10, 30);
  });

  it('submits nutrition, clears editing state, and reloads data', async () => {
    vi.mocked(bodyApi.logNutrition).mockResolvedValue({ id: 'log-1' } as never);
    const { result } = renderHook(() => useNutritionTab());

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.onSubmit({
        date: '2026-03-27',
        source: 'Manual',
        calories: 2200,
        protein_grams: 180,
        carbs_grams: null,
        fat_grams: 70,
      });
    });

    expect(bodyApi.logNutrition).toHaveBeenCalledWith({
      date: '2026-03-27',
      source: 'Manual',
      calories: 2200,
      protein_grams: 180,
      fat_grams: 70,
    });
    expect(mockNotifications.success).toHaveBeenCalled();
    expect(result.current.isSaving).toBe(false);
    expect(result.current.editingId).toBeNull();
  });

  it('handles stats and logs load failures', async () => {
    vi.mocked(bodyApi.getNutritionStats).mockRejectedValue(new Error('stats failed'));
    vi.mocked(bodyApi.getNutritionLogs).mockRejectedValue(new Error('logs failed'));

    const { result } = renderHook(() => useNutritionTab());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(mockNotifications.error).toHaveBeenCalledTimes(2);
  });

  it('handles submit and delete failures', async () => {
    vi.mocked(bodyApi.logNutrition).mockRejectedValue(new Error('save failed'));
    vi.mocked(bodyApi.deleteNutritionLog).mockRejectedValue(new Error('delete failed'));

    const { result } = renderHook(() => useNutritionTab());

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.onSubmit({
        date: '2026-03-27',
        source: 'Manual',
        calories: 2200,
        protein_grams: 180,
        carbs_grams: null,
        fat_grams: 70,
      });
      await result.current.deleteEntry('log-1');
    });

    expect(mockNotifications.error).toHaveBeenCalledTimes(2);
    expect(result.current.isSaving).toBe(false);
  });

  it('supports editing, canceling edit, and pagination helpers', async () => {
    const { result } = renderHook(() => useNutritionTab());

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => {
      result.current.editEntry({
        id: 'log-1',
        date: '2026-03-21T10:00:00Z',
        source: 'Manual',
        calories: 2100,
        protein_grams: 170,
        carbs_grams: 200,
        fat_grams: 60,
      } as never);
    });

    expect(result.current.isEditing).toBe(true);
    expect(result.current.editingId).toBe('log-1');
    expect(window.scrollTo).toHaveBeenCalled();

    act(() => {
      result.current.nextPage();
      result.current.prevPage();
      result.current.changePage(3);
      result.current.cancelEdit();
    });

    expect(bodyApi.getNutritionLogs).toHaveBeenCalledWith(2, 10, undefined);
    expect(bodyApi.getNutritionLogs).toHaveBeenCalledWith(1, 10, undefined);
    expect(bodyApi.getNutritionLogs).toHaveBeenCalledWith(3, 10, undefined);
    expect(result.current.isEditing).toBe(false);
  });
});
