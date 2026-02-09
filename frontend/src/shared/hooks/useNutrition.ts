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
}

interface NutritionActions {
  fetchLogs: (page?: number, days?: number) => Promise<void>;
  fetchStats: () => Promise<void>;
  createLog: (data: CreateNutritionLogRequest) => Promise<void>;
  deleteLog: (id: string) => Promise<void>;
  reset: () => void;
}

type NutritionStore = NutritionState & NutritionActions;

/**
 * Nutrition store using Zustand
 * 
 * Manages nutrition logs, daily stats, and diet adherence tracking.
 */
export const useNutritionStore = create<NutritionStore>((set, get) => ({
  logs: [],
  stats: null,
  total: 0,
  page: 1,
  totalPages: 0,
  isLoading: false,
  error: null,

  fetchLogs: async (page = 1, days) => {
    set({ isLoading: true, error: null });
    try {
      const params = new URLSearchParams();
      params.append('page', page.toString());
      if (days) {
        params.append('days', days.toString());
      }

      const response = await httpClient<NutritionListResponse>(`/nutrition/list?${params.toString()}`);
      
      if (response) {
        set({
          logs: response.logs,
          total: response.total,
          page: response.page,
          totalPages: response.total_pages,
        });
      }
      set({ isLoading: false });
    } catch (error) {
      console.error('Error fetching nutrition logs:', error);
      set({ 
        isLoading: false, 
        error: 'Falha ao carregar histórico nutricional.' 
      });
    }
  },

  fetchStats: async () => {
    set({ isLoading: true });
    try {
      const stats = await httpClient<NutritionStats>('/nutrition/stats');
      set({ stats: stats ?? null, isLoading: false });
    } catch (error) {
      console.error('Error fetching nutrition stats:', error);
      set({ isLoading: false });
    }
  },

  createLog: async (data: CreateNutritionLogRequest) => {
    set({ isLoading: true, error: null });
    try {
      await httpClient<NutritionLog>('/nutrition/log', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      await Promise.all([get().fetchLogs(), get().fetchStats()]);
    } catch (error) {
      console.error('Error creating nutrition log:', error);
      set({ 
        isLoading: false, 
        error: 'Falha ao salvar registro nutricional.' 
      });
      throw error;
    }
  },

  deleteLog: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      await httpClient(`/nutrition/${id}`, { method: 'DELETE' });
      
      const { logs, total } = get();
      set({
        logs: logs.filter((l) => l.id !== id),
        total: total - 1,
        isLoading: false,
      });
      // Optionally refresh stats
      void get().fetchStats();
    } catch (error) {
      console.error('Error deleting nutrition log:', error);
      set({ 
        isLoading: false, 
        error: 'Falha ao excluir registro.' 
      });
      throw error;
    }
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
