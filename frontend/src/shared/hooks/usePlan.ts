import { create } from 'zustand';

import { httpClient } from '../api/http-client';
import type { Plan } from '../types/plan';

interface PlanState {
  plan: Plan | null;
  isLoading: boolean;
  error: string | null;
  fetchPlan: () => Promise<void>;
  setPlan: (plan: Plan | null) => void;
  clearPlan: () => void;
  reset: () => void;
}

interface BackendPlanPayload {
  id?: string;
  title?: string;
  goal?: {
    primary?: string;
    objective_summary?: string;
  };
  timeline?: {
    start_date?: string;
    target_date?: string;
    review_cadence?: string;
  };
  strategy?: {
    rationale?: string;
    adaptation_policy?: string;
    constraints?: string[];
    preferences?: string[];
    current_risks?: string[];
  };
  nutrition_strategy?: {
    daily_targets?: {
      calories?: number;
      protein_g?: number;
      carbs_g?: number;
      fat_g?: number;
      fiber_g?: number;
    };
    adherence_notes?: string[];
  };
  training_program?: {
    split_name?: string;
    frequency_per_week?: number;
    session_duration_min?: number;
    routines?: {
      id?: string;
      name?: string;
      objective?: string;
      exercises?: {
        name?: string;
        sets?: number;
        reps?: string;
        load_guidance?: string;
      }[];
    }[];
    weekly_schedule?: {
      day?: string;
      routine_id?: string;
      focus?: string;
      type?: string;
    }[];
  };
  checkpoints?: {
    checkpoint_at?: string;
    summary?: string;
    decision?: string;
    next_focus?: string;
    evidence?: string[];
  }[];
  current_summary?: {
    active_focus?: string;
  };
  updated_at?: string;
}

function formatPlanDate(value: string | undefined): string {
  if (!value) return '';
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return value;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value.split('T')[0] ?? value;
  }
  return parsed.toISOString().split('T')[0] ?? value;
}

function mapBackendToPlan(payload: BackendPlanPayload): Plan {
  const checkpoints = payload.checkpoints ?? [];
  const latestCheckpoint = checkpoints.length > 0 ? checkpoints[checkpoints.length - 1] : undefined;
  const nutritionTargets = payload.nutrition_strategy?.daily_targets ?? {};

  return {
    overview: {
      id: payload.id ?? 'plan',
      title: payload.title ?? 'Plano Mestre',
      objective_summary: payload.goal?.objective_summary ?? 'Objetivo nao definido',
      start_date: formatPlanDate(payload.timeline?.start_date),
      target_date: formatPlanDate(payload.timeline?.target_date),
      review_cadence: payload.timeline?.review_cadence ?? 'Nao definido',
      active_focus: payload.current_summary?.active_focus ?? 'Sem foco definido',
      last_updated_at: payload.updated_at ?? new Date().toISOString(),
    },
    strategy: {
      rationale: payload.strategy?.rationale ?? 'Sem racional definido',
      adaptation_policy: payload.strategy?.adaptation_policy ?? 'Sem politica definida',
      constraints: payload.strategy?.constraints ?? [],
      preferences: payload.strategy?.preferences ?? [],
      current_risks: payload.strategy?.current_risks ?? [],
    },
    nutrition_targets: {
      calories: nutritionTargets.calories ?? 0,
      protein_g: nutritionTargets.protein_g ?? 0,
      carbs_g: nutritionTargets.carbs_g,
      fat_g: nutritionTargets.fat_g,
      fiber_g: nutritionTargets.fiber_g,
    },
    adherence_notes: payload.nutrition_strategy?.adherence_notes ?? [],
    training_program: {
      split_name: payload.training_program?.split_name ?? 'Nao definido',
      frequency_per_week: payload.training_program?.frequency_per_week ?? 0,
      session_duration_min: payload.training_program?.session_duration_min ?? 0,
      routines: (payload.training_program?.routines ?? []).map((routine, index) => ({
        id: routine.id ?? `routine-${String(index + 1)}`,
        name: routine.name ?? `Rotina ${String(index + 1)}`,
        objective: routine.objective,
        exercises: (routine.exercises ?? []).map((exercise) => ({
          name: exercise.name ?? 'Exercicio',
          sets: exercise.sets ?? 0,
          reps: exercise.reps ?? '-',
          load_guidance: exercise.load_guidance ?? '-',
        })),
      })),
      weekly_schedule: (payload.training_program?.weekly_schedule ?? []).map((item) => ({
        day: item.day ?? '-',
        routine_id: item.routine_id,
        focus: item.focus ?? '-',
        type: item.type ?? 'training',
      })),
    },
    latest_checkpoint: latestCheckpoint
      ? {
          id: latestCheckpoint.checkpoint_at ?? 'checkpoint',
          occurred_at: latestCheckpoint.checkpoint_at ?? '',
          summary: latestCheckpoint.summary ?? '',
          decision: latestCheckpoint.decision ?? '',
          next_focus: latestCheckpoint.next_focus ?? '',
          evidence: latestCheckpoint.evidence ?? [],
        }
      : null,
  };
}

function normalizePlanPayload(payload: unknown): Plan | null {
  if (!payload) return null;
  if (typeof payload !== 'object') return null;

  const asRecord = payload as Record<string, unknown>;
  if ('overview' in asRecord && 'training_program' in asRecord) {
    return payload as Plan;
  }

  return mapBackendToPlan(payload as BackendPlanPayload);
}

export const usePlanStore = create<PlanState>((set) => ({
  plan: null,
  isLoading: false,
  error: null,

  fetchPlan: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await httpClient('/plan');
      set({ plan: normalizePlanPayload(data), isLoading: false, error: null });
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
