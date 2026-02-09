import { create } from 'zustand';

import { httpClient } from '../api/http-client';
import type { DashboardData } from '../types/dashboard';

interface DashboardState {
  data: DashboardData | null;
  isLoading: boolean;
  error: string | null;
}

interface DashboardActions {
  fetchData: () => Promise<void>;
  reset: () => void;
}

type DashboardStore = DashboardState & DashboardActions;

/**
 * Dashboard store using Zustand
 * 
 * Manages the global state for the dashboard, including stats and recent activities.
 */
export const useDashboardStore = create<DashboardStore>((set) => ({
  data: null,
  isLoading: false,
  error: null,

  fetchData: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await httpClient<DashboardData>('/dashboard');
      set({ data, isLoading: false });
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      set({ 
        isLoading: false, 
        error: 'Failed to fetch dashboard data' 
      });
    }
  },

  reset: () => {
    set({ data: null, isLoading: false, error: null });
  },
}));
