import { create } from 'zustand';

import { httpClient } from '../api/http-client';
import type { 
  NutritionListResponse, 
  NutritionLog, 
  NutritionStats,
  CreateNutritionLogRequest
} from '../types/nutrition';

interface NutritionState {
  logs: NutritionLog[];
  stats: NutritionStats | null;
  total: number;
  page: number;
  totalPages: number;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  fetchLogs: (page?: number, limit?: number) => Promise<void>;
  fetchStats: () => Promise<void>;
  createLog: (data: CreateNutritionLogRequest) => Promise<void>;
  deleteLog: (id: string) => Promise<void>;
  reset: () => void;
}

/**
 * Standardized Nutrition Store.
 */
export const useNutritionStore = create<NutritionState>((set, get) => ({
  logs: [],
  stats: null,
  total: 0,
  page: 1,
  totalPages: 0,
  isLoading: false,
  error: null,

  fetchLogs: async (page = 1, limit = 20) => {
    set({ isLoading: true, error: null });
    try {
      const data = await httpClient<NutritionListResponse>(
        `/nutrition/list?page=${String(page)}&page_size=${String(limit)}`
      );
      if (data) {
        set({
          logs: data.logs,
          total: data.total,
          page: data.page,
          totalPages: data.total_pages,
          isLoading: false
        });
      } else {
        set({ isLoading: false });
      }
    } catch (err) {
      set({ 
        error: err instanceof Error ? err.message : 'Error fetching nutrition logs', 
        isLoading: false 
      });
    }
  },

  fetchStats: async () => {
    try {
      const data = await httpClient<NutritionStats>('/nutrition/stats');
      if (data) set({ stats: data });
    } catch {
      // Quiet fail for stats
    }
  },

  createLog: async (data: CreateNutritionLogRequest) => {
    set({ isLoading: true });
    try {
      await httpClient('/nutrition/log', { method: 'POST', body: JSON.stringify(data) });
      await Promise.all([get().fetchLogs(), get().fetchStats()]);
    } catch (err) {
      set({ 
        isLoading: false, 
        error: err instanceof Error ? err.message : 'Error creating nutrition log' 
      });
      throw err;
    }
  },

  deleteLog: async (id: string) => {
    await httpClient(`/nutrition/${id}`, { method: 'DELETE' });
    const { logs, total } = get();
    set({
      logs: logs.filter(log => log.id !== id),
      total: total - 1
    });
  },

  reset: () => {
    set({
      logs: [],
      stats: null,
      total: 0,
      page: 1,
      totalPages: 0,
      isLoading: false,
      error: null,
    });
  },
}));
