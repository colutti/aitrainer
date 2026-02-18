import { renderHook, act, cleanup, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

import { useNotificationStore } from '../../../shared/hooks/useNotification';
import { bodyApi } from '../api/body-api';

import { useWeightTab } from './useWeightTab';

vi.mock('../api/body-api', () => ({
  bodyApi: {
    getBodyCompositionStats: vi.fn(),
    getWeightHistory: vi.fn(),
    logWeight: vi.fn(),
    deleteWeight: vi.fn(),
  },
}));

const mockNotify = { success: vi.fn(), error: vi.fn() };

vi.mock('../../../shared/hooks/useNotification', () => ({
  useNotificationStore: vi.fn(),
}));

// Suppress jsdom's window.scrollTo not-implemented error
Object.defineProperty(window, 'scrollTo', { value: vi.fn(), writable: true });

const mockLogEntry = {
  id: 'log-1',
  date: '2024-01-15',
  weight_kg: 80,
  body_fat_pct: 20,
};

const mockHistory = {
  logs: [{ ...mockLogEntry, muscle_mass_pct: 40 }],
  total: 1, page: 1, total_pages: 1,
};

const emptyHistory = { logs: [], total: 0, page: 1, page_size: 10, total_pages: 0 };

const mockStats = { current_weight: 80, target_weight: 75 };

describe('useWeightTab hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useNotificationStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue(mockNotify);
    vi.mocked(bodyApi.getBodyCompositionStats).mockResolvedValue(mockStats as unknown as Awaited<ReturnType<typeof bodyApi.getBodyCompositionStats>>);
    vi.mocked(bodyApi.getWeightHistory).mockResolvedValue(emptyHistory as Awaited<ReturnType<typeof bodyApi.getWeightHistory>>);
  });

  afterEach(() => {
    cleanup();
  });

  it('should handle submit success', async () => {
    vi.mocked(bodyApi.getWeightHistory).mockResolvedValue(mockHistory as Awaited<ReturnType<typeof bodyApi.getWeightHistory>>);
    vi.mocked(bodyApi.logWeight).mockResolvedValue({} as Awaited<ReturnType<typeof bodyApi.logWeight>>);

    const { result } = renderHook(() => useWeightTab());
    await waitFor(() => { expect(result.current.isLoading).toBe(false); });

    await act(async () => {
      result.current.editEntry(mockLogEntry as Parameters<typeof result.current.editEntry>[0]);
      await (result.current.handleSubmit as () => Promise<void>)();
    });

    expect(bodyApi.logWeight).toHaveBeenCalled();
    expect(mockNotify.success).toHaveBeenCalledWith('Registro de peso salvo!');
  });

  it('should handle submit error', async () => {
    vi.mocked(bodyApi.getWeightHistory).mockResolvedValue(mockHistory as Awaited<ReturnType<typeof bodyApi.getWeightHistory>>);
    vi.mocked(bodyApi.logWeight).mockRejectedValue(new Error('fail'));

    const { result } = renderHook(() => useWeightTab());
    await waitFor(() => { expect(result.current.isLoading).toBe(false); });

    await act(async () => {
      result.current.editEntry(mockLogEntry as Parameters<typeof result.current.editEntry>[0]);
      await (result.current.handleSubmit as () => Promise<void>)();
    });

    expect(mockNotify.error).toHaveBeenCalledWith('Erro ao salvar registro de peso.');
  });

  it('starts with isEditing=false and editingDate=null', async () => {
    const { result } = renderHook(() => useWeightTab());
    await act(async () => { await Promise.resolve(); });

    expect(result.current.isEditing).toBe(false);
    expect(result.current.editingDate).toBeNull();
  });

  it('editEntry sets isEditing=true and tracks the date', async () => {
    const { result } = renderHook(() => useWeightTab());
    await act(async () => { await Promise.resolve(); });

    act(() => { result.current.editEntry(mockLogEntry as Parameters<typeof result.current.editEntry>[0]); });

    expect(result.current.isEditing).toBe(true);
    expect(result.current.editingDate).toBe('2024-01-15');
  });

  it('cancelEdit clears isEditing and editingDate', async () => {
    const { result } = renderHook(() => useWeightTab());
    await act(async () => { await Promise.resolve(); });

    act(() => { result.current.editEntry(mockLogEntry as Parameters<typeof result.current.editEntry>[0]); });
    act(() => { result.current.cancelEdit(); });

    expect(result.current.isEditing).toBe(false);
    expect(result.current.editingDate).toBeNull();
  });

  it('editEntry with another log replaces editingDate', async () => {
    const { result } = renderHook(() => useWeightTab());
    await act(async () => { await Promise.resolve(); });

    act(() => { result.current.editEntry(mockLogEntry as Parameters<typeof result.current.editEntry>[0]); });
    act(() => { result.current.editEntry({ ...mockLogEntry, id: 'log-2', date: '2024-02-20' } as Parameters<typeof result.current.editEntry>[0]); });

    expect(result.current.editingDate).toBe('2024-02-20');
  });
});
