import { beforeEach, describe, expect, it, vi } from 'vitest';

import { httpClient } from '../../shared/api/http-client';
import { usePlanStore } from '../../shared/hooks/usePlan';
import type { PlanViewModel } from '../../shared/types/plan';
import { render, screen, waitFor, fireEvent } from '../../shared/utils/test-utils';

import PlanPage from './PlanPage';

const mockNavigate = vi.fn();

vi.mock('../../shared/api/http-client', () => ({
  httpClient: vi.fn(),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const activePlan: PlanViewModel = {
  status: 'ACTIVE_PLAN',
  generic_response_notice: 'Plano ativo deve ser a fonte primária.',
  active_plan: {
    title: 'Plano Base Força',
    goal_summary: 'Aumentar força sem perder aderência',
    success_metrics: ['3 treinos/semana', 'Peso estável'],
    training_split: 'Upper Lower',
    weekly_schedule: [
      { day: 'monday', routine_name: 'Upper A', focus: 'Peito', exercise_names: ['Supino'], is_rest_day: false, is_today: true },
      { day: 'tuesday', routine_name: null, focus: 'Recuperação', exercise_names: [], is_rest_day: true, is_today: false },
      { day: 'wednesday', routine_name: 'Lower A', focus: 'Pernas', exercise_names: ['Agachamento'], is_rest_day: false, is_today: false },
    ],
    today_training: {
      day: 'monday',
      routine_name: 'Upper A',
      focus: 'Peito',
      exercise_names: ['Supino'],
      is_rest_day: false,
    },
    nutrition_targets: {
      calories_kcal: 2500,
      protein_g: 160,
      carbs_g: 280,
      fat_g: 70,
    },
    current_risks: [],
  },
  progress: {
    plan_id: 'plan-1',
    generated_at: '2026-06-28T10:00:00Z',
    training_adherence: { status: 'on_track', details: 'Treinos em dia.' },
    nutrition_adherence: { status: 'off_track', details: 'Proteína abaixo do alvo.' },
    progression_status: 'maintaining',
    body_trend_status: 'aligned',
    conflicts: [],
    recommended_review: false,
    evidence_summary: ['Treinos consistentes', 'Peso estável'],
  },
};

describe('PlanPage runtime', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    usePlanStore.getState().reset();
    mockNavigate.mockReset();
  });

  it('loads the active plan from the API and renders the runtime data path', async () => {
    vi.mocked(httpClient).mockResolvedValue(activePlan);

    render(<PlanPage />, { route: '/dashboard/plan' });

    expect(screen.getByTestId('plan-skeleton')).toBeInTheDocument();

    await waitFor(() => {
      expect(httpClient).toHaveBeenCalledWith('/plan/view');
    });

    await waitFor(() => {
      expect(screen.getByText('Plano Base Força')).toBeInTheDocument();
    });

    expect(screen.getByTestId('plan-view')).toBeInTheDocument();
    expect(screen.getByText('2500 kcal')).toBeInTheDocument();
    expect(screen.getByText('Treinos consistentes Peso estável')).toBeInTheDocument();
  });

  it('renders the empty/discovery state returned by the API and opens chat with the plan draft', async () => {
    vi.mocked(httpClient).mockResolvedValue({
      status: 'DISCOVERY_IN_PROGRESS',
      generic_response_notice: 'Ainda faltam dados para gerar o plano.',
      discovery: {
        missing_fields: ['target_date', 'constraints'],
        collected_fields: ['goal_primary'],
        next_prompt: 'Qual é o prazo?',
      },
    });

    render(<PlanPage />, { route: '/dashboard/plan' });

    await waitFor(() => {
      expect(screen.getByTestId('plan-discovery-view')).toBeInTheDocument();
    });

    expect(screen.getByText('Ainda faltam dados para gerar o plano.')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Criar plano no chat|Create.*plan|Crear.*plan/i }));

    expect(mockNavigate).toHaveBeenCalledWith('/dashboard/chat', {
      state: {
        draftMessage: 'Qual é o prazo?',
      },
    });
  });

  it('falls back to the generic draft message when discovery next_prompt is blank', async () => {
    vi.mocked(httpClient).mockResolvedValue({
      status: 'DISCOVERY_IN_PROGRESS',
      generic_response_notice: 'Ainda faltam dados para gerar o plano.',
      discovery: {
        missing_fields: ['target_date'],
        collected_fields: ['goal_primary'],
        next_prompt: '   ',
      },
    });

    render(<PlanPage />, { route: '/dashboard/plan' });

    await waitFor(() => {
      expect(screen.getByTestId('plan-discovery-view')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Criar plano no chat|Create.*plan|Crear.*plan/i }));

    expect(mockNavigate).toHaveBeenCalledWith('/dashboard/chat', {
      state: {
        draftMessage: 'Crie meu plano mestre de treino e nutrição.',
      },
    });
  });

  it('falls back to the empty-state CTA when the API request fails', async () => {
    vi.mocked(httpClient).mockRejectedValue(new Error('plan unavailable'));

    render(<PlanPage />, { route: '/dashboard/plan' });

    await waitFor(() => {
      expect(screen.getByText('Nenhum plano encontrado')).toBeInTheDocument();
    });

    expect(usePlanStore.getState().error).toBe('plan unavailable');
  });
});
