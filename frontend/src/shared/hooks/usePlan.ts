import { create } from 'zustand';

import { httpClient } from '../api/http-client';
import type { Plan } from '../types/plan';

interface PlanState {
  activePlan: Plan | null;
  isLoading: boolean;
  error: string | null;
  fetchActivePlan: () => Promise<void>;
  setActivePlan: (plan: Plan | null) => void;
  clearActivePlan: () => void;
  reset: () => void;
}

export const usePlanStore = create<PlanState>((set) => ({
  activePlan: null,
  isLoading: false,
  error: null,

  fetchActivePlan: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await httpClient<Plan>('/plan/active');
      set({ activePlan: data ?? null, isLoading: false, error: null });
    } catch (error) {
      set({
        isLoading: false,
        activePlan: null,
        error: error instanceof Error ? error.message : 'Error fetching active plan',
      });
    }
  },

  setActivePlan: (plan) => {
    set({ activePlan: plan });
  },

  clearActivePlan: () => {
    set({ activePlan: null });
  },

  reset: () => {
    set({ activePlan: null, isLoading: false, error: null });
  },
}));
