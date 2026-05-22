import { beforeEach, describe, expect, it, vi } from 'vitest';

import { httpClient } from '../api/http-client';
import type { PlanViewModel } from '../types/plan';

import { usePlanStore } from './usePlan';

vi.mock('../api/http-client', () => ({
  httpClient: vi.fn(),
}));

const mockPlan: PlanViewModel = {
  status: 'ACTIVE_PLAN',
  generic_response_notice: 'O plano ativo agora e a fonte primaria.',
  active_plan: {
    title: 'Plano Mestre',
    goal_summary: 'Ganhar massa mantendo aderencia',
    success_metrics: ['Peso: 75 kg'],
    training_split: 'Upper Lower',
    weekly_schedule: [
      { day: 'monday', routine_name: 'Upper A', focus: 'Peito', exercise_names: ['Supino'], is_rest_day: false, is_today: true },
      { day: 'tuesday', routine_name: null, focus: 'Recuperacao', exercise_names: [], is_rest_day: true, is_today: false },
      { day: 'wednesday', routine_name: 'Lower A', focus: 'Pernas', exercise_names: ['Agachamento'], is_rest_day: false, is_today: false },
      { day: 'thursday', routine_name: null, focus: 'Recuperacao', exercise_names: [], is_rest_day: true, is_today: false },
      { day: 'friday', routine_name: 'Upper B', focus: 'Costas', exercise_names: ['Remada'], is_rest_day: false, is_today: false },
      { day: 'saturday', routine_name: null, focus: 'Recuperacao', exercise_names: [], is_rest_day: true, is_today: false },
      { day: 'sunday', routine_name: null, focus: 'Recuperacao', exercise_names: [], is_rest_day: true, is_today: false },
    ],
    today_training: {
      day: 'monday',
      routine_name: 'Upper A',
      focus: 'Peito',
      exercise_names: ['Supino'],
      is_rest_day: false,
    },
    nutrition_targets: {
      calories_kcal: 2600,
      protein_g: 160,
      carbs_g: 300,
      fat_g: 75,
    },
    current_risks: [],
    next_review_at: '2026-06-01',
    latest_review_summary: 'Aderencia boa',
  },
  progress: {
    plan_id: 'plan-1',
    generated_at: '2026-05-22T10:00:00Z',
    training_adherence: { status: 'on_track', details: '3 treino(s) registrado(s) recentemente.' },
    nutrition_adherence: { status: 'insufficient_data', details: 'Sem logs nutricionais suficientes.' },
    progression_status: 'maintaining',
    body_trend_status: 'insufficient_data',
    conflicts: [],
    recommended_review: false,
    evidence_summary: ['Treinos presentes'],
  },
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

  it('fetches the backend view model successfully', async () => {
    vi.mocked(httpClient).mockResolvedValue(mockPlan);

    await usePlanStore.getState().fetchPlan();

    const state = usePlanStore.getState();
    expect(httpClient).toHaveBeenCalledWith('/plan/view');
    expect(state.plan).toEqual(mockPlan);
    expect(state.error).toBeNull();
  });

  it('stores discovery view models as-is', async () => {
    vi.mocked(httpClient).mockResolvedValue({
      status: 'DISCOVERY_IN_PROGRESS',
      generic_response_notice: 'Sem plano ativo, a IA deve marcar a resposta como generica.',
      discovery: {
        missing_fields: ['target_date'],
        collected_fields: ['goal_primary'],
        next_prompt: 'Coletar: data alvo.',
      },
    });

    await usePlanStore.getState().fetchPlan();

    const state = usePlanStore.getState();
    expect(state.plan?.status).toBe('DISCOVERY_IN_PROGRESS');
    expect(state.plan?.discovery?.missing_fields).toEqual(['target_date']);
  });

  it('handles empty plan response', async () => {
    vi.mocked(httpClient).mockResolvedValue(undefined);

    await usePlanStore.getState().fetchPlan();

    const state = usePlanStore.getState();
    expect(state.plan).toBeNull();
    expect(state.error).toBeNull();
  });

  it('stores error when fetch fails', async () => {
    vi.mocked(httpClient).mockRejectedValue(new Error('plan unavailable'));

    await usePlanStore.getState().fetchPlan();

    const state = usePlanStore.getState();
    expect(state.plan).toBeNull();
    expect(state.error).toBe('plan unavailable');
  });

  it('updates plan locally', () => {
    usePlanStore.getState().setPlan(mockPlan);
    expect(usePlanStore.getState().plan).toEqual(mockPlan);

    usePlanStore.getState().clearPlan();
    expect(usePlanStore.getState().plan).toBeNull();
  });
});
