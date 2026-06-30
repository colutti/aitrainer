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
    updateWeight: vi.fn(),
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
      await result.current.handleSubmit(result.current.onSubmit)();
    });

    expect(bodyApi.logWeight).toHaveBeenCalled();
    expect(mockNotify.success).toHaveBeenCalledWith('Registro de peso salvo!');
  });

  it('uses updateWeight with the edited log id instead of creating a new entry', async () => {
    vi.mocked(bodyApi.getWeightHistory).mockResolvedValue(mockHistory as Awaited<ReturnType<typeof bodyApi.getWeightHistory>>);
    vi.mocked(bodyApi.updateWeight).mockResolvedValue({} as Awaited<ReturnType<typeof bodyApi.updateWeight>>);

    const { result } = renderHook(() => useWeightTab());
    await waitFor(() => { expect(result.current.isLoading).toBe(false); });

    act(() => {
      result.current.editEntry({
        ...mockLogEntry,
        muscle_mass_kg: 34.6,
        waist_cm: 83,
        notes: 'updated entry',
      } as Parameters<typeof result.current.editEntry>[0]);
    });

    await act(async () => {
      await result.current.onSubmit({
        date: '2024-01-15',
        weight_kg: 79.4,
        body_fat_pct: 18.7,
        muscle_mass_kg: 34.6,
        body_water_pct: 56.4,
        bone_mass_kg: 3.2,
        visceral_fat: 7,
        bmr: 1740,
        notes: 'updated entry',
        neck_cm: 38,
        chest_cm: 102,
        waist_cm: 83,
        hips_cm: 97,
        bicep_r_cm: 35,
        bicep_l_cm: 34,
        thigh_r_cm: 56,
        thigh_l_cm: 55,
        calf_r_cm: 36,
        calf_l_cm: 35,
      });
    });

    expect(bodyApi.updateWeight).toHaveBeenCalledWith('log-1', 79.4, {
      date: '2024-01-15',
      weight_kg: 79.4,
      body_fat_pct: 18.7,
      muscle_mass_kg: 34.6,
      body_water_pct: 56.4,
      bone_mass_kg: 3.2,
      visceral_fat: 7,
      bmr: 1740,
      notes: 'updated entry',
      neck_cm: 38,
      chest_cm: 102,
      waist_cm: 83,
      hips_cm: 97,
      bicep_r_cm: 35,
      bicep_l_cm: 34,
      thigh_r_cm: 56,
      thigh_l_cm: 55,
      calf_r_cm: 36,
      calf_l_cm: 35,
    });
    expect(bodyApi.logWeight).not.toHaveBeenCalled();
    expect(result.current.isEditing).toBe(false);
    expect(result.current.editingDate).toBeNull();
  });

  it('should handle submit error', async () => {
    vi.mocked(bodyApi.getWeightHistory).mockResolvedValue(mockHistory as Awaited<ReturnType<typeof bodyApi.getWeightHistory>>);
    vi.mocked(bodyApi.logWeight).mockRejectedValue(new Error('fail'));

    const { result } = renderHook(() => useWeightTab());
    await waitFor(() => { expect(result.current.isLoading).toBe(false); });

    await act(async () => {
      result.current.editEntry(mockLogEntry as Parameters<typeof result.current.editEntry>[0]);
      await result.current.handleSubmit(result.current.onSubmit)();
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
