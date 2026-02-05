import { create } from 'zustand';

import { httpClient } from '../api/http-client';
import type { 
  WeightLog, 
  BodyCompositionStats 
} from '../types/body';

interface BodyState {
  logs: WeightLog[];
  stats: BodyCompositionStats | null;
  isLoading: boolean;
  error: string | null;
}

interface BodyActions {
  fetchLogs: (limit?: number) => Promise<void>;
  fetchStats: () => Promise<void>;
  logWeight: (data: Partial<WeightLog>) => Promise<void>;
  deleteLog: (date: string) => Promise<void>;
  reset: () => void;
}

type BodyStore = BodyState & BodyActions;

/**
 * Body store using Zustand
 * 
 * Manages weight logs and body composition trends.
 */
export const useBodyStore = create<BodyStore>((set, get) => ({
  logs: [],
  stats: null,
  isLoading: false,
  error: null,

  fetchLogs: async (limit = 30) => {
    set({ isLoading: true, error: null });
    try {
      const response = await httpClient<WeightLog[]>(`/weight?limit=${limit.toString()}`);
      set({ logs: response ?? [], isLoading: false });
    } catch (error) {
      console.error('Error fetching weight logs:', error);
      set({ 
        isLoading: false, 
        error: 'Falha ao carregar histórico de peso.' 
      });
    }
  },

  fetchStats: async () => {
    set({ isLoading: true });
    try {
      const stats = await httpClient<BodyCompositionStats>('/weight/stats');
      set({ stats, isLoading: false });
    } catch (error) {
      console.error('Error fetching body stats:', error);
      set({ isLoading: false });
    }
  },

  logWeight: async (data: Partial<WeightLog>) => {
    set({ isLoading: true, error: null });
    try {
      await httpClient('/weight', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      await Promise.all([get().fetchLogs(), get().fetchStats()]);
    } catch (error) {
      console.error('Error logging weight:', error);
      set({ 
        isLoading: false, 
        error: 'Falha ao registrar peso.' 
      });
      throw error;
    }
  },

  deleteLog: async (date: string) => {
    set({ isLoading: true, error: null });
    try {
      await httpClient(`/weight/${date}`, { method: 'DELETE' });
      
      const { logs } = get();
      set({
        logs: logs.filter((l) => l.date !== date),
        isLoading: false,
      });
      void get().fetchStats();
    } catch (error) {
      console.error('Error deleting weight log:', error);
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
      isLoading: false,
      error: null,
    });
  },
}));
