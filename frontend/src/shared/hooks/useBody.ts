import { create } from 'zustand';

import { httpClient } from '../api/http-client';
import type { 
  WeightLog, 
  BodyCompositionStats,
  WeightListResponse 
} from '../types/body';

interface BodyState {
  logs: WeightLog[];
  stats: BodyCompositionStats | null;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  fetchLogs: (limit?: number) => Promise<void>;
  fetchStats: () => Promise<void>;
  logWeight: (data: Partial<WeightLog>) => Promise<void>;
  deleteLog: (date: string) => Promise<void>;
  reset: () => void;
}

/**
 * Standardized Body Store.
 */
export const useBodyStore = create<BodyState>((set, get) => ({
  logs: [],
  stats: null,
  isLoading: false,
  error: null,

  fetchLogs: async (limit = 30) => {
    set({ isLoading: true, error: null });
    try {
      const data = await httpClient<WeightListResponse>(`/weight?limit=${String(limit)}`);
      if (data) set({ logs: data.logs, isLoading: false });
    } catch (err) {
      set({ 
        error: err instanceof Error ? err.message : 'Error fetching logs', 
        isLoading: false 
      });
    }
  },

  fetchStats: async () => {
    try {
      const data = await httpClient<BodyCompositionStats>('/metabolism/stats');
      if (data) set({ stats: data });
    } catch {
      // Quiet fail for stats
    }
  },

  logWeight: async (data: Partial<WeightLog>) => {
    set({ isLoading: true });
    try {
      await httpClient('/weight', { method: 'POST', body: JSON.stringify(data) });
      await Promise.all([get().fetchLogs(), get().fetchStats()]);
    } catch (err) {
      set({ 
        isLoading: false, 
        error: err instanceof Error ? err.message : 'Error logging weight' 
      });
      throw err;
    }
  },

  deleteLog: async (date: string) => {
    set({ isLoading: true });
    try {
      await httpClient(`/weight/${date}`, { method: 'DELETE' });
      await Promise.all([get().fetchLogs(), get().fetchStats()]);
    } catch (err) {
      set({ 
        isLoading: false, 
        error: err instanceof Error ? err.message : 'Error deleting log' 
      });
      throw err;
    }
  },

  reset: () => {
    set({
      logs: [],
      stats: null,
      isLoading: false,
      error: null,
    });
  },
}));
