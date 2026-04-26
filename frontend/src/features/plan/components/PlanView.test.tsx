import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { Plan } from '../../../shared/types/plan';

import { PlanView } from './PlanView';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, number>) => {
      if (key === 'plan.labels.week_of' && params) {
        return `week ${String(params.week)}/${String(params.total)}`;
      }
      return key;
    },
    i18n: { language: 'en-US' },
  }),
}));

const mockPlan: Plan = {
  overview: {
    id: 'plan-1',
    title: 'Plano Recomp Rafael - V19',
    objective_summary: 'Perder gordura mantendo performance',
    start_date: '2026-04-01',
    target_date: '2026-06-01',
    review_cadence: 'quinzenal',
    active_focus: 'consistencia',
    last_updated_at: '2026-04-19T10:00:00Z',
  },
  strategy: {
    rationale: 'Maintain / Recomposition',
    adaptation_policy: 'ajustes por evidencia',
    constraints: ['viagens'],
    preferences: ['treino de manha'],
    current_risks: ['sono ruim'],
  },
  nutrition_targets: {
    calories: 2200,
    protein_g: 180,
    carbs_g: 220,
    fat_g: 70,
    fiber_g: 35,
  },
  adherence_notes: ['Consistent tracking', 'Progressive overload'],
  training_program: {
    split_name: 'push_pull_legs',
    frequency_per_week: 5,
    session_duration_min: 60,
    weekly_schedule: [
      { day: 'monday', routine_id: 'push_a', focus: 'push', type: 'training' },
      { day: 'tuesday', routine_id: 'pull_a', focus: 'pull', type: 'training' },
    ],
    routines: [
      {
        id: 'push_a',
        name: 'Push A',
        objective: 'forca',
        exercises: [{ name: 'Supino Reto', sets: 4, reps: '6-8', load_guidance: 'RPE 8' }],
      },
      {
        id: 'pull_a',
        name: 'Pull A',
        objective: 'hipertrofia',
        exercises: [{ name: 'Remada', sets: 4, reps: '8-10', load_guidance: 'RPE 8.5' }],
      },
    ],
  },
  latest_checkpoint: {
    id: 'checkpoint-1',
    occurred_at: '2026-04-17T08:00:00Z',
    summary: 'Aderencia acima da meta',
    decision: 'manter estrategia',
    next_focus: 'qualidade do sono',
    evidence: ['peso em queda'],
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

  it('renders redesigned plan view with nutrition values', () => {
    render(<PlanView plan={mockPlan} isLoading={false} onOpenChat={vi.fn()} />);

    expect(screen.getByText('Plano Recomp Rafael - V19')).toBeInTheDocument();
    expect(screen.getByText('plan.sections.nutrition_strategy')).toBeInTheDocument();
    expect(screen.getByText('2200')).toBeInTheDocument();
    expect(screen.getAllByText('plan.sections.daily_routine').length).toBeGreaterThan(0);
    expect(screen.getByText('plan.sections.latest_checkpoint')).toBeInTheDocument();
  });

  it('switches weekly exercises when changing selected day', () => {
    render(<PlanView plan={mockPlan} isLoading={false} onOpenChat={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: /tue/i }));

    const weeklyArea = screen.getByTestId('plan-weekly-exercises');
    expect(within(weeklyArea).getByText('Remada')).toBeInTheDocument();
  });

  it('shows recovery cta when selected day has no routine', () => {
    const onOpenChat = vi.fn();
    render(<PlanView plan={mockPlan} isLoading={false} onOpenChat={onOpenChat} />);

    fireEvent.click(screen.getByRole('button', { name: /wed/i }));

    expect(screen.getByText('plan.labels.rest_day')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'plan.empty.cta' }));
    expect(onOpenChat).toHaveBeenCalledTimes(1);
  });
});
