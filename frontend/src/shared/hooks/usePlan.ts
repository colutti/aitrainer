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

interface BackendCheckpoint {
  checkpoint_at?: string;
  summary?: string;
  ai_assessment?: string;
  decision?: string;
  next_step?: string;
}

interface BackendActivePlan {
  id?: string;
  status?: string;
  title?: string;
  objective_summary?: string;
  start_date?: string;
  end_date?: string;
  execution?: {
    today_training?: unknown;
    today_nutrition?: unknown;
    upcoming_days?: unknown[];
    active_focus?: string;
  };
  tracking?: {
    checkpoints?: BackendCheckpoint[];
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

function normalizeTodayTraining(value: unknown): string[] {
  if (typeof value === 'string' && value.trim()) {
    return [value.trim()];
  }
  if (value && typeof value === 'object') {
    const record = value as Record<string, unknown>;
    const title = record.title;
    const summary = record.summary;
    const session = record.session as Record<string, unknown> | undefined;
    const rawExercises = Array.isArray(session?.exercises)
      ? session.exercises
      : Array.isArray(record.exercises)
        ? record.exercises
        : [];
    const exercises = rawExercises
      .filter((exercise): exercise is Record<string, unknown> => !!exercise && typeof exercise === 'object')
      .map((exercise) => {
        const name = typeof exercise.name === 'string' ? exercise.name : 'Exercicio';
        const sets =
          typeof exercise.sets === 'number' || typeof exercise.sets === 'string'
            ? String(exercise.sets)
            : '-';
        const reps = typeof exercise.reps === 'string' ? exercise.reps : '-';
        const load = typeof exercise.load_guidance === 'string'
          ? exercise.load_guidance
          : typeof exercise.weight === 'number' || typeof exercise.weight === 'string'
            ? `${String(exercise.weight)}kg`
            : 'carga livre';
        return `${name} - ${sets}x${reps} (${load})`;
      });
    if (typeof title === 'string' && title.trim()) {
      return exercises.length > 0 ? [title.trim(), ...exercises] : [title.trim()];
    }
    if (exercises.length > 0) return exercises;
    if (typeof summary === 'string' && summary.trim()) return [summary.trim()];
  }
  return ['Sem treino definido'];
}

function normalizeExerciseDetails(value: unknown): string[] {
  const rawExercises = Array.isArray(value) ? value : [];
  return rawExercises
    .filter((exercise): exercise is Record<string, unknown> => !!exercise && typeof exercise === 'object')
    .map((exercise) => {
      const name = typeof exercise.name === 'string' ? exercise.name : 'Exercicio';
      const sets =
        typeof exercise.sets === 'number' || typeof exercise.sets === 'string'
          ? String(exercise.sets)
          : '-';
      const reps = typeof exercise.reps === 'string' ? exercise.reps : '-';
      const load = typeof exercise.load_guidance === 'string'
        ? exercise.load_guidance
        : typeof exercise.weight === 'number' || typeof exercise.weight === 'string'
          ? `${String(exercise.weight)}kg`
          : 'carga livre';
      return `${name} - ${sets}x${reps} (${load})`;
    });
}

function normalizeTodayNutrition(value: unknown): string[] {
  if (typeof value === 'string' && value.trim()) {
    return [value.trim()];
  }
  if (value && typeof value === 'object') {
    const record = value as Record<string, unknown>;
    const calories = record.calories;
    const protein = record.protein_target;
    const caloriesText = typeof calories === 'number' ? String(calories) : '-';
    const proteinText = typeof protein === 'number' ? String(protein) : '-';
    if (typeof calories === 'number' || typeof protein === 'number') {
      return [`${caloriesText} kcal / ${proteinText}g proteina`];
    }
  }
  return ['Sem nutricao definida'];
}

function normalizeUpcomingDays(value: unknown[]): Plan['upcoming_days'] {
  if (value.length === 0) return [];
  return value.map((item, index) => {
    if (item && typeof item === 'object') {
      const record = item as Record<string, unknown>;
      const trainingField = record.training;
      const trainingAsText = typeof trainingField === 'string'
        ? trainingField
        : trainingField && typeof trainingField === 'object'
          ? typeof (trainingField as Record<string, unknown>).title === 'string'
            ? String((trainingField as Record<string, unknown>).title)
            : 'Treino nao definido'
          : 'Treino nao definido';
      const trainingRecord = trainingField && typeof trainingField === 'object'
        ? (trainingField as Record<string, unknown>)
        : undefined;
      const trainingDetailsFromSession = normalizeExerciseDetails(
        trainingRecord?.session && typeof trainingRecord.session === 'object'
          ? (trainingRecord.session as Record<string, unknown>).exercises
          : undefined
      );
      const trainingDetailsFromDirect = normalizeExerciseDetails(trainingRecord?.exercises);
      const trainingDetailsFromRecord = normalizeExerciseDetails(record.training_exercises);
      const trainingDetails = [
        ...trainingDetailsFromSession,
        ...trainingDetailsFromDirect,
        ...trainingDetailsFromRecord,
      ];
      return {
        date: typeof record.date === 'string' ? record.date : `day-${String(index)}`,
        label: typeof record.label === 'string' ? record.label : `Dia ${String(index + 1)}`,
        training: trainingAsText,
        training_details: trainingDetails,
        nutrition: typeof record.nutrition === 'string' ? record.nutrition : 'Nutricao nao definida',
        status:
          record.status === 'planned' || record.status === 'adjusted' || record.status === 'rest'
            ? record.status
            : 'planned',
      };
    }
    return {
      date: `day-${String(index)}`,
      label: `Dia ${String(index + 1)}`,
      training: String(item),
      training_details: [],
      nutrition: 'Nutricao nao definida',
      status: 'planned',
    };
  });
}

function mapStatusTone(status: string | undefined): Plan['status_banner']['tone'] {
  if (status === 'active') return 'on_track';
  if (status === 'awaiting_approval') return 'awaiting_approval';
  if (status === 'adjustment_pending_approval') return 'pending_review';
  return 'attention';
}

function mapBackendToPlan(payload: BackendActivePlan): Plan {
  const checkpoints = payload.tracking?.checkpoints ?? [];
  const latestCheckpoint = checkpoints.length > 0 ? checkpoints[checkpoints.length - 1] : undefined;

  return {
    overview: {
      id: payload.id ?? 'plan',
      title: payload.title ?? 'Plano',
      objective_summary: payload.objective_summary ?? 'Objetivo nao definido',
      status:
        payload.status === 'draft' ||
        payload.status === 'awaiting_approval' ||
        payload.status === 'active' ||
        payload.status === 'adjustment_pending_approval' ||
        payload.status === 'completed' ||
        payload.status === 'archived'
          ? payload.status
          : 'draft',
      start_date: formatPlanDate(payload.start_date),
      end_date: formatPlanDate(payload.end_date),
      progress_percent: 0,
      active_focus: payload.execution?.active_focus ?? 'Sem foco definido',
      last_updated_at: payload.updated_at ?? new Date().toISOString(),
    },
    mission_today: {
      training: normalizeTodayTraining(payload.execution?.today_training),
      nutrition: normalizeTodayNutrition(payload.execution?.today_nutrition),
      coaching: latestCheckpoint?.ai_assessment ?? '',
    },
    upcoming_days: normalizeUpcomingDays(payload.execution?.upcoming_days ?? []),
    latest_checkpoint: latestCheckpoint
      ? {
          id: latestCheckpoint.checkpoint_at ?? 'checkpoint',
          occurred_at: latestCheckpoint.checkpoint_at ?? '',
          summary: latestCheckpoint.summary ?? '',
          ai_assessment: latestCheckpoint.ai_assessment ?? '',
          decision: latestCheckpoint.decision ?? '',
          next_step: latestCheckpoint.next_step ?? '',
        }
      : null,
    status_banner: {
      tone: mapStatusTone(payload.status),
      message: payload.status === 'awaiting_approval' ? 'Aguardando aprovacao' : 'Plano carregado',
    },
  };
}

function normalizePlanPayload(payload: unknown): Plan | null {
  if (!payload) return null;
  if (typeof payload !== 'object') return null;

  const asRecord = payload as Record<string, unknown>;
  if ('overview' in asRecord && 'mission_today' in asRecord) {
    return payload as Plan;
  }

  return mapBackendToPlan(payload as BackendActivePlan);
}

export const usePlanStore = create<PlanState>((set) => ({
  activePlan: null,
  isLoading: false,
  error: null,

  fetchActivePlan: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await httpClient('/plan/active');
      set({ activePlan: normalizePlanPayload(data), isLoading: false, error: null });
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
