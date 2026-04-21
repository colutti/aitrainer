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
    title: 'Plano de Recomposicao',
    objective_summary: 'Ganhar massa magra mantendo gordura sob controle',
    status: 'active',
    start_date: '2026-04-01',
    end_date: '2026-06-01',
    progress_percent: 42,
    active_focus: 'Consistencia semanal de treinos',
    last_updated_at: '2026-04-19T10:00:00Z',
  },
  mission_today: {
    training: ['Treino A - peitoral e triceps'],
    nutrition: ['2100 kcal', 'Proteina >= 160g'],
    coaching: 'Durma 7h30 para melhorar recuperacao.',
  },
  upcoming_days: [
    {
      date: '2026-04-20',
      label: 'Amanha',
      training: 'Treino B - costas e biceps',
      training_details: ['Remada Curvada - 4x8 (RPE 8)'],
      nutrition: '2200 kcal com foco em carbo pre-treino',
      status: 'planned',
    },
  ],
  latest_checkpoint: {
    id: 'checkpoint-1',
    occurred_at: '2026-04-17T08:00:00Z',
    summary: 'Boa aderencia na semana.',
    ai_assessment: 'A progressao de carga esta adequada.',
    decision: 'Manter estrategia atual com ajuste leve de calorias.',
    next_step: 'Reavaliar em 4 dias.',
  },
  status_banner: {
    tone: 'on_track',
    message: 'Plano no ritmo certo.',
  },
};

describe('usePlanStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    usePlanStore.getState().reset();
  });

  it('starts with empty state', () => {
    const state = usePlanStore.getState();
    expect(state.activePlan).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('fetches active plan successfully', async () => {
    vi.mocked(httpClient).mockResolvedValue(mockPlan);

    await usePlanStore.getState().fetchActivePlan();

    const state = usePlanStore.getState();
    expect(httpClient).toHaveBeenCalledWith('/plan/active');
    expect(state.activePlan).toEqual(mockPlan);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('normalizes backend ActivePlan payload into PlanView shape', async () => {
    vi.mocked(httpClient).mockResolvedValue({
      id: 'plan-backend-1',
      user_email: 'rafacolucci@gmail.com',
      status: 'active',
      title: 'Plano Atual',
      objective_summary: 'Perder gordura mantendo desempenho',
      start_date: '2026-04-01T00:00:00Z',
      end_date: '2026-06-01T00:00:00Z',
      version: 2,
      strategy: {
        primary_goal: 'lose_fat',
        success_criteria: ['consistencia semanal'],
        constraints: ['viagem quinta'],
        coaching_rationale: 'deficit moderado',
        adaptation_policy: 'approval_required',
      },
      execution: {
        today_training: {
          title: 'Lower A',
          session: {
            exercises: [
              { name: 'Agachamento', sets: 4, reps: '6-8', load_guidance: 'RPE 8' },
            ],
          },
        },
        today_nutrition: { calories: 2200, protein_target: 170 },
        upcoming_days: [
          {
            date: '2026-04-20',
            label: 'Amanha',
            training: {
              title: 'Upper B',
              session: {
                exercises: [
                  { name: 'Supino Reto', sets: 4, reps: '6-8', load_guidance: 'RPE 8' },
                ],
              },
            },
            nutrition: '2300 kcal',
            status: 'planned',
          },
        ],
        active_focus: 'consistencia',
        current_risks: ['sono ruim'],
        pending_changes: [],
      },
      tracking: {
        checkpoints: [
          {
            checkpoint_at: '2026-04-19T10:00:00Z',
            summary: 'Aderencia boa',
            ai_assessment: 'mantem rota',
            decision: 'continuar',
            next_step: 'revisar em 4 dias',
          },
        ],
        adherence_snapshot: { training: 'good', nutrition: 'mixed' },
        progress_snapshot: { status: 'on_track' },
        last_ai_assessment: 'boa semana',
        last_user_acknowledgement: null,
      },
      governance: {
        change_reason: null,
        approval_request: null,
      },
      created_at: '2026-04-01T00:00:00Z',
      updated_at: '2026-04-19T10:00:00Z',
    });

    await usePlanStore.getState().fetchActivePlan();

    const state = usePlanStore.getState();
    expect(state.activePlan?.overview.title).toBe('Plano Atual');
    expect(state.activePlan?.overview.id).toBe('plan-backend-1');
    expect(state.activePlan?.overview.start_date).toBe('2026-04-01');
    expect(state.activePlan?.overview.end_date).toBe('2026-06-01');
    expect(state.activePlan?.mission_today.training[0]).toContain('Lower A');
    expect(state.activePlan?.mission_today.training[1]).toContain(
      'Agachamento - 4x6-8 (RPE 8)'
    );
    expect(state.activePlan?.upcoming_days[0]?.training_details[0]).toContain(
      'Supino Reto - 4x6-8 (RPE 8)'
    );
    expect(state.activePlan?.mission_today.nutrition[0]).toContain('2200');
    expect(state.activePlan?.status_banner.tone).toBe('on_track');
  });

  it('adds fallback upcoming days when backend payload has none', async () => {
    vi.mocked(httpClient).mockResolvedValue({
      id: 'plan-backend-2',
      status: 'active',
      title: 'Plano sem dias',
      objective_summary: 'Ajustar rotina',
      start_date: '2026-04-01T00:00:00Z',
      end_date: '2026-06-01T00:00:00Z',
      execution: {
        today_training: {},
        today_nutrition: {},
        upcoming_days: [],
        active_focus: 'consistencia',
      },
      tracking: { checkpoints: [] },
    });

    await usePlanStore.getState().fetchActivePlan();
    const state = usePlanStore.getState();

    expect(state.activePlan?.upcoming_days).toEqual([]);
  });

  it('handles empty active plan response', async () => {
    vi.mocked(httpClient).mockResolvedValue(undefined);

    await usePlanStore.getState().fetchActivePlan();

    const state = usePlanStore.getState();
    expect(state.activePlan).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('stores error when fetch fails', async () => {
    vi.mocked(httpClient).mockRejectedValue(new Error('plan unavailable'));

    await usePlanStore.getState().fetchActivePlan();

    const state = usePlanStore.getState();
    expect(state.activePlan).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBe('plan unavailable');
  });

  it('updates active plan locally', () => {
    usePlanStore.getState().setActivePlan(mockPlan);
    expect(usePlanStore.getState().activePlan).toEqual(mockPlan);

    usePlanStore.getState().clearActivePlan();
    expect(usePlanStore.getState().activePlan).toBeNull();
  });
});
