import { create } from 'zustand';

import { httpClient } from '../api/http-client';
import type { PlanViewModel } from '../types/plan';

interface PlanState {
  plan: PlanViewModel | null;
  isLoading: boolean;
  error: string | null;
  fetchPlan: () => Promise<void>;
  setPlan: (plan: PlanViewModel | null) => void;
  clearPlan: () => void;
  reset: () => void;
}

export const usePlanStore = create<PlanState>((set) => ({
  plan: null,
  isLoading: false,
  error: null,

  fetchPlan: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await httpClient('/plan/view');
      const plan = data ? (data as PlanViewModel) : null;
      set({ plan, isLoading: false, error: null });
    } catch (error) {
      set({
        isLoading: false,
        plan: null,
        error: error instanceof Error ? error.message : 'Error fetching plan',
      });
    }
  },

  setPlan: (plan) => {
    set({ plan });
  },

  clearPlan: () => {
    set({ plan: null });
  },

  reset: () => {
    set({ plan: null, isLoading: false, error: null });
  },
}));
