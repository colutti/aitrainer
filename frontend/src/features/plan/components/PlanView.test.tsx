import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { PlanViewModel } from '../../../shared/types/plan';

import { PlanView } from './PlanView';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

const activePlan: PlanViewModel = {
  status: 'ACTIVE_PLAN',
  generic_response_notice: 'O plano ativo agora e a fonte primaria.',
  active_plan: {
    title: 'Plano Mestre Hipertrofia',
    goal_summary: 'Ganhar massa magra com superavit controlado',
    success_metrics: ['Peso: 75 kg', 'Aderencia: 85 %'],
    training_split: 'Upper Lower',
    weekly_schedule: [
      { day: 'monday', routine_name: 'Upper A', focus: 'Peito e costas', exercise_names: ['Supino Reto', 'Remada Curvada'], is_rest_day: false, is_today: true },
      { day: 'tuesday', routine_name: null, focus: 'Recuperacao', exercise_names: [], is_rest_day: true, is_today: false },
      { day: 'wednesday', routine_name: 'Lower A', focus: 'Pernas', exercise_names: ['Agachamento Livre'], is_rest_day: false, is_today: false },
      { day: 'thursday', routine_name: null, focus: 'Recuperacao', exercise_names: [], is_rest_day: true, is_today: false },
      { day: 'friday', routine_name: 'Upper B', focus: 'Upper', exercise_names: ['Remada Curvada'], is_rest_day: false, is_today: false },
      { day: 'saturday', routine_name: null, focus: 'Recuperacao', exercise_names: [], is_rest_day: true, is_today: false },
      { day: 'sunday', routine_name: null, focus: 'Recuperacao', exercise_names: [], is_rest_day: true, is_today: false },
    ],
    today_training: {
      day: 'monday',
      routine_name: 'Upper A',
      focus: 'Peito e costas',
      exercise_names: ['Supino Reto', 'Remada Curvada'],
      is_rest_day: false,
    },
    nutrition_targets: {
      calories_kcal: 2600,
      protein_g: 160,
      carbs_g: 315,
      fat_g: 75,
    },
    current_risks: ['Sono irregular'],
    next_review_at: '2026-06-01',
    latest_review_summary: 'Aderencia consistente na ultima semana',
  },
  progress: {
    plan_id: 'plan-1',
    generated_at: '2026-05-22T10:00:00Z',
    training_adherence: { status: 'on_track', details: '3 treino(s) registrado(s) recentemente.' },
    nutrition_adherence: { status: 'insufficient_data', details: 'Sem logs nutricionais suficientes.' },
    progression_status: 'maintaining',
    body_trend_status: 'insufficient_data',
    conflicts: [{ kind: 'goal_energy_mismatch', message: 'Conflito de energia detectado.' }],
    recommended_review: true,
    evidence_summary: ['Treinos presentes', 'Nutricao insuficiente'],
  },
};

describe('PlanView', () => {
  it('shows loading skeleton', () => {
    render(<PlanView plan={null} isLoading onOpenChat={vi.fn()} />);
    expect(screen.getByTestId('plan-skeleton')).toBeInTheDocument();
  });

  it('renders empty state when there is no plan', () => {
    const onOpenChat = vi.fn();
    render(<PlanView plan={null} isLoading={false} onOpenChat={onOpenChat} />);

    expect(screen.getByText('plan.empty.title')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'plan.empty.cta' }));
    expect(onOpenChat).toHaveBeenCalledTimes(1);
  });

  it('hides discovery details when plan is missing but discovery exists', () => {
    const onOpenChat = vi.fn();
    render(
      <PlanView
        plan={{
          status: 'DISCOVERY_IN_PROGRESS',
          generic_response_notice: 'Sem plano ativo, a IA deve tratar a resposta como generica.',
          discovery: {
            missing_fields: ['target_date', 'constraints'],
            collected_fields: ['goal_primary', 'goal_summary'],
            next_prompt: 'Coletar: data alvo.',
          },
        }}
        isLoading={false}
        onOpenChat={onOpenChat}
      />,
    );

    expect(screen.getByTestId('plan-discovery-view')).toBeInTheDocument();
    expect(screen.queryByText('Coletar: data alvo.')).not.toBeInTheDocument();
    expect(screen.queryByText('plan.sections.discovery')).not.toBeInTheDocument();
    expect(screen.queryByText('plan.labels.collected_fields')).not.toBeInTheDocument();
    expect(screen.queryByText('plan.labels.missing_fields')).not.toBeInTheDocument();
  });

  it('renders active plan view with progress and nutrition', () => {
    render(<PlanView plan={activePlan} isLoading={false} onOpenChat={vi.fn()} />);

    expect(screen.getByText('Plano Mestre Hipertrofia')).toBeInTheDocument();
    expect(screen.getByTestId('plan-weekly-schedule')).toBeInTheDocument();
    expect(within(screen.getByTestId('plan-weekly-schedule')).getByText('plan.days.monday')).toBeInTheDocument();
    expect(screen.getByText('2600 kcal')).toBeInTheDocument();
    expect(screen.getByText('Supino Reto')).toBeInTheDocument();
    expect(screen.getByText('Conflito de energia detectado.')).toBeInTheDocument();
    expect(screen.queryByText('O plano ativo agora e a fonte primaria.')).not.toBeInTheDocument();
  });

  it('switches the daily routine when a weekly day is selected', () => {
    render(<PlanView plan={activePlan} isLoading={false} onOpenChat={vi.fn()} />);

    expect(within(screen.getByTestId('plan-daily-routine')).getByText('Upper A')).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText('plan.days.wednesday'));
    expect(within(screen.getByTestId('plan-daily-routine')).getByText('Lower A')).toBeInTheDocument();
    expect(within(screen.getByTestId('plan-daily-routine')).getByText('Agachamento Livre')).toBeInTheDocument();
  });

  it('shows chat cta when a rest day is selected', () => {
    const onOpenChat = vi.fn();
    render(
      <PlanView
        plan={{
          ...activePlan,
          active_plan: {
            ...activePlan.active_plan!,
            today_training: {
              day: 'monday',
              focus: 'recuperacao',
              exercise_names: [],
              is_rest_day: true,
            },
          },
        }}
        isLoading={false}
        onOpenChat={onOpenChat}
      />,
    );

    fireEvent.click(screen.getByLabelText('plan.days.tuesday'));
    expect(screen.getByText('plan.labels.rest_day')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'plan.empty.cta' }));
    expect(onOpenChat).toHaveBeenCalledTimes(1);
  });

  it('renders exercise list inside the daily routine area', () => {
    render(<PlanView plan={activePlan} isLoading={false} onOpenChat={vi.fn()} />);

    const exerciseArea = screen.getByTestId('plan-weekly-exercises');
    expect(within(exerciseArea).getByText('Remada Curvada')).toBeInTheDocument();
  });
});
