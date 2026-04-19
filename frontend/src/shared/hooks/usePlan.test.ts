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
