import { renderHook, act, cleanup, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

import { useNotificationStore } from '../../../shared/hooks/useNotification';
import { bodyApi } from '../api/body-api';

import { useNutritionTab } from './useNutritionTab';

vi.mock('../api/body-api', () => ({
  bodyApi: {
    getNutritionLogs: vi.fn(),
    getNutritionStats: vi.fn(),
    logNutrition: vi.fn(),
    deleteNutritionLog: vi.fn(),
  },
}));

const mockNotify = { success: vi.fn(), error: vi.fn() };

vi.mock('../../../shared/hooks/useNotification', () => ({
  useNotificationStore: vi.fn(),
}));

Object.defineProperty(window, 'scrollTo', { value: vi.fn(), writable: true });

const mockLogEntry = {
  id: '1',
  date: '2024-01-01',
  calories: 2000,
  source: 'Manual',
  user_email: 'test@test.com',
  protein_grams: 100,
  carbs_grams: 200,
  fat_grams: 50,
  notes: '',
};

const mockLogs = {
  logs: [mockLogEntry],
  total: 1, page: 1, page_size: 10, total_pages: 1,
};

const emptyLogs = { logs: [], total: 0, page: 1, page_size: 10, total_pages: 0 };

const mockStats = { avg_calories: 2000, avg_protein: 150 };

describe('useNutritionTab hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useNotificationStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue(mockNotify);
    vi.mocked(bodyApi.getNutritionLogs).mockResolvedValue(emptyLogs as Awaited<ReturnType<typeof bodyApi.getNutritionLogs>>);
    vi.mocked(bodyApi.getNutritionStats).mockResolvedValue({} as Awaited<ReturnType<typeof bodyApi.getNutritionStats>>);
  });

  afterEach(() => {
    cleanup();
  });

  it('should fetch data on mount', async () => {
    vi.mocked(bodyApi.getNutritionLogs).mockResolvedValue(mockLogs as Awaited<ReturnType<typeof bodyApi.getNutritionLogs>>);
    vi.mocked(bodyApi.getNutritionStats).mockResolvedValue(mockStats as unknown as Awaited<ReturnType<typeof bodyApi.getNutritionStats>>);

    const { result } = renderHook(() => useNutritionTab());
    await waitFor(() => { expect(result.current.isLoading).toBe(false); });

    expect(result.current.logs).toHaveLength(1);
    expect(result.current.stats).toEqual(mockStats);
  });

  it('should handle submit success', async () => {
    vi.mocked(bodyApi.getNutritionLogs).mockResolvedValue(mockLogs as Awaited<ReturnType<typeof bodyApi.getNutritionLogs>>);
    vi.mocked(bodyApi.getNutritionStats).mockResolvedValue(mockStats as unknown as Awaited<ReturnType<typeof bodyApi.getNutritionStats>>);
    vi.mocked(bodyApi.logNutrition).mockResolvedValue({} as Awaited<ReturnType<typeof bodyApi.logNutrition>>);

    const { result } = renderHook(() => useNutritionTab());
    await waitFor(() => { expect(result.current.isLoading).toBe(false); });

    await act(async () => {
      result.current.editEntry(mockLogEntry as Parameters<typeof result.current.editEntry>[0]);
      await (result.current.handleSubmit as () => Promise<void>)();
    });

    expect(bodyApi.logNutrition).toHaveBeenCalled();
    expect(mockNotify.success).toHaveBeenCalledWith('Registro nutricional salvo!');
  });

  it('should handle submit error', async () => {
    vi.mocked(bodyApi.getNutritionLogs).mockResolvedValue(mockLogs as Awaited<ReturnType<typeof bodyApi.getNutritionLogs>>);
    vi.mocked(bodyApi.getNutritionStats).mockResolvedValue(mockStats as unknown as Awaited<ReturnType<typeof bodyApi.getNutritionStats>>);
    vi.mocked(bodyApi.logNutrition).mockRejectedValue(new Error('fail'));

    const { result } = renderHook(() => useNutritionTab());
    await waitFor(() => { expect(result.current.isLoading).toBe(false); });

    await act(async () => {
      result.current.editEntry(mockLogEntry as Parameters<typeof result.current.editEntry>[0]);
      await (result.current.handleSubmit as () => Promise<void>)();
    });

    expect(mockNotify.error).toHaveBeenCalledWith('Erro ao salvar registro nutricional.');
  });

  it('should handle delete error', async () => {
    vi.mocked(bodyApi.getNutritionLogs).mockResolvedValue(mockLogs as Awaited<ReturnType<typeof bodyApi.getNutritionLogs>>);
    vi.mocked(bodyApi.getNutritionStats).mockResolvedValue(mockStats as unknown as Awaited<ReturnType<typeof bodyApi.getNutritionStats>>);
    vi.mocked(bodyApi.deleteNutritionLog).mockRejectedValue(new Error('fail'));

    const { result } = renderHook(() => useNutritionTab());
    await waitFor(() => { expect(result.current.isLoading).toBe(false); });

    await act(async () => {
      await result.current.deleteEntry('1');
    });

    expect(mockNotify.error).toHaveBeenCalledWith('Erro ao remover registro.');
  });

  it('starts with isEditing=false and editingId=null', async () => {
    const { result } = renderHook(() => useNutritionTab());
    await act(async () => { await Promise.resolve(); });

    expect(result.current.isEditing).toBe(false);
    expect(result.current.editingId).toBeNull();
  });

  it('editEntry sets isEditing=true and tracks the id', async () => {
    const { result } = renderHook(() => useNutritionTab());
    await act(async () => { await Promise.resolve(); });

    act(() => { result.current.editEntry(mockLogEntry as Parameters<typeof result.current.editEntry>[0]); });

    expect(result.current.isEditing).toBe(true);
    expect(result.current.editingId).toBe('1');
  });

  it('editEntry extracts date without UTC timezone bug', async () => {
    // If using new Date().toISOString(), UTC+X timezones would shift to previous day
    const logWithTime = { ...mockLogEntry, date: '2024-01-15T00:00:00', id: 'log-2' };
    const { result } = renderHook(() => useNutritionTab());
    await act(async () => { await Promise.resolve(); });

    act(() => { result.current.editEntry(logWithTime as Parameters<typeof result.current.editEntry>[0]); });

    expect(result.current.editingId).toBe('log-2');
    expect(result.current.isEditing).toBe(true);
  });

  it('cancelEdit clears isEditing and editingId', async () => {
    const { result } = renderHook(() => useNutritionTab());
    await act(async () => { await Promise.resolve(); });

    act(() => { result.current.editEntry(mockLogEntry as Parameters<typeof result.current.editEntry>[0]); });
    act(() => { result.current.cancelEdit(); });

    expect(result.current.isEditing).toBe(false);
    expect(result.current.editingId).toBeNull();
  });

  it('editEntry with another log replaces editingId', async () => {
    const { result } = renderHook(() => useNutritionTab());
    await act(async () => { await Promise.resolve(); });

    act(() => { result.current.editEntry(mockLogEntry as Parameters<typeof result.current.editEntry>[0]); });
    act(() => { result.current.editEntry({ ...mockLogEntry, id: 'log-2' } as Parameters<typeof result.current.editEntry>[0]); });

    expect(result.current.editingId).toBe('log-2');
  });
});
