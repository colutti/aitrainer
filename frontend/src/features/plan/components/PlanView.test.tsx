import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { Plan } from '../../../shared/types/plan';

import { PlanView } from './PlanView';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: 'pt-BR' },
  }),
}));

const mockPlan: Plan = {
  overview: {
    id: 'plan-1',
    title: 'Plano Mestre',
    objective_summary: 'Perder gordura mantendo performance',
    start_date: '2026-04-01',
    target_date: '2026-06-01',
    review_cadence: 'quinzenal',
    active_focus: 'consistencia',
    last_updated_at: '2026-04-19T10:00:00Z',
  },
  strategy: {
    rationale: 'Deficit moderado com foco em forca',
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
  },
  adherence_notes: ['manter hidratacao'],
  training_program: {
    split_name: 'push_pull_legs',
    frequency_per_week: 5,
    session_duration_min: 60,
    weekly_schedule: [{ day: 'monday', routine_id: 'push_a', focus: 'push', type: 'training' }],
    routines: [
      {
        id: 'push_a',
        name: 'Push A',
        objective: 'forca',
        exercises: [{ name: 'Supino Reto', sets: 4, reps: '6-8', load_guidance: 'RPE 8' }],
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

  it('renders master plan sections', () => {
    render(<PlanView plan={mockPlan} isLoading={false} onOpenChat={vi.fn()} />);

    expect(screen.getByText('Plano Mestre')).toBeInTheDocument();
    expect(screen.getByText('plan.sections.strategy')).toBeInTheDocument();
    expect(screen.getByText('plan.sections.nutrition_targets')).toBeInTheDocument();
    expect(screen.getByText('plan.sections.training_program')).toBeInTheDocument();
    expect(screen.getByText('plan.sections.weekly_schedule')).toBeInTheDocument();
    expect(screen.getByText('plan.sections.routines')).toBeInTheDocument();
    expect(screen.getByText('Supino Reto - 4x6-8 (RPE 8)')).toBeInTheDocument();
    expect(screen.getByText('plan.sections.latest_checkpoint')).toBeInTheDocument();
  });
});
