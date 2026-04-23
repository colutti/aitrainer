import { beforeEach, describe, expect, it, vi } from 'vitest';

import { httpClient } from '../api/http-client';
import type { Plan } from '../types/plan';

import { usePlanStore } from './usePlan';

vi.mock('../api/http-client', () => ({
  httpClient: vi.fn(),
}));

const mockPlan: Plan = {
  overview: {
    id: 'plan-1',
    title: 'Plano Mestre',
    objective_summary: 'Ganhar massa magra mantendo gordura sob controle',
    start_date: '2026-04-01',
    target_date: '2026-06-01',
    review_cadence: 'quinzenal',
    active_focus: 'consistencia semanal de treinos',
    last_updated_at: '2026-04-19T10:00:00Z',
  },
  strategy: {
    rationale: 'Progressao de carga com deficit leve',
    adaptation_policy: 'ajustes por evidencia',
    constraints: [],
    preferences: [],
    current_risks: [],
  },
  nutrition_targets: {
    calories: 2200,
    protein_g: 180,
  },
  adherence_notes: [],
  training_program: {
    split_name: 'upper_lower',
    frequency_per_week: 4,
    session_duration_min: 55,
    weekly_schedule: [{ day: 'monday', routine_id: 'upper_a', focus: 'upper', type: 'training' }],
    routines: [{ id: 'upper_a', name: 'Upper A', exercises: [{ name: 'Supino', sets: 4, reps: '6-8', load_guidance: 'RPE 8' }] }],
  },
  latest_checkpoint: null,
};

describe('usePlanStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    usePlanStore.getState().reset();
  });

  it('starts with empty state', () => {
    const state = usePlanStore.getState();
    expect(state.plan).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('fetches plan successfully', async () => {
    vi.mocked(httpClient).mockResolvedValue(mockPlan);

    await usePlanStore.getState().fetchPlan();

    const state = usePlanStore.getState();
    expect(httpClient).toHaveBeenCalledWith('/plan');
    expect(state.plan).toEqual(mockPlan);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('normalizes backend plan payload into master-plan view model', async () => {
    vi.mocked(httpClient).mockResolvedValue({
      id: 'plan-backend-1',
      title: 'Plano Atual',
      goal: {
        primary: 'lose_fat',
        objective_summary: 'Perder gordura mantendo desempenho',
      },
      timeline: {
        start_date: '2026-04-01T00:00:00Z',
        target_date: '2026-06-01T00:00:00Z',
        review_cadence: 'semanal',
      },
      strategy: {
        rationale: 'deficit moderado',
        adaptation_policy: 'approval_required',
      },
      nutrition_strategy: {
        daily_targets: { calories: 2200, protein_g: 170 },
      },
      training_program: {
        split_name: 'upper_lower',
        frequency_per_week: 4,
        session_duration_min: 50,
        weekly_schedule: [{ day: 'monday', routine_id: 'upper_a', focus: 'upper', type: 'training' }],
        routines: [
          {
            id: 'upper_a',
            name: 'Upper A',
            exercises: [{ name: 'Supino Reto', sets: 4, reps: '6-8', load_guidance: 'RPE 8' }],
          },
        ],
      },
      current_summary: {
        active_focus: 'consistencia',
      },
      checkpoints: [
        {
          checkpoint_at: '2026-04-19T10:00:00Z',
          summary: 'Aderencia boa',
          decision: 'continuar',
          next_focus: 'recuperacao',
          evidence: ['treino completo'],
        },
      ],
      updated_at: '2026-04-19T10:00:00Z',
    });

    await usePlanStore.getState().fetchPlan();

    const state = usePlanStore.getState();
    expect(state.plan?.overview.title).toBe('Plano Atual');
    expect(state.plan?.overview.start_date).toBe('2026-04-01');
    expect(state.plan?.nutrition_targets.calories).toBe(2200);
    expect(state.plan?.training_program.routines[0]?.name).toBe('Upper A');
    expect(state.plan?.latest_checkpoint?.decision).toBe('continuar');
  });

  it('handles empty plan response', async () => {
    vi.mocked(httpClient).mockResolvedValue(undefined);

    await usePlanStore.getState().fetchPlan();

    const state = usePlanStore.getState();
    expect(state.plan).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('stores error when fetch fails', async () => {
    vi.mocked(httpClient).mockRejectedValue(new Error('plan unavailable'));

    await usePlanStore.getState().fetchPlan();

    const state = usePlanStore.getState();
    expect(state.plan).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBe('plan unavailable');
  });

  it('updates plan locally', () => {
    usePlanStore.getState().setPlan(mockPlan);
    expect(usePlanStore.getState().plan).toEqual(mockPlan);

    usePlanStore.getState().clearPlan();
    expect(usePlanStore.getState().plan).toBeNull();
  });
});
