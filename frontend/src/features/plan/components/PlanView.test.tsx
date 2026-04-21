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
    title: 'Plano Central',
    objective_summary: 'Perder gordura mantendo performance',
    status: 'active',
    start_date: '2026-04-01',
    end_date: '2026-06-01',
    progress_percent: 35,
    active_focus: 'Treino de forca com deficit leve',
    last_updated_at: '2026-04-19T10:00:00Z',
  },
  mission_today: {
    training: ['Treino A - 50min', 'Agachamento - 4x6-8 (RPE 8)'],
    nutrition: ['Meta 2100 kcal', 'Proteina >= 160g'],
    coaching: 'Priorizar hidratacao no periodo da tarde.',
  },
  upcoming_days: [
    {
      date: '2026-04-20',
      label: 'Amanha',
      training: 'Treino B',
      training_details: ['Supino Reto - 4x6-8 (RPE 8)'],
      nutrition: '2200 kcal',
      status: 'planned',
    },
    {
      date: '2026-04-21',
      label: 'Ter',
      training: 'Mobilidade e caminhada',
      training_details: [],
      nutrition: '2000 kcal',
      status: 'adjusted',
    },
  ],
  latest_checkpoint: {
    id: 'checkpoint-1',
    occurred_at: '2026-04-17T08:00:00Z',
    summary: 'Aderencia acima da meta.',
    ai_assessment: 'Recuperacao melhorou apos ajuste de sono.',
    decision: 'Manter estrategia e revisar em 5 dias.',
    next_step: 'Revisao no dia 22.',
  },
  status_banner: {
    tone: 'on_track',
    message: 'Plano em execucao consistente.',
  },
};

describe('PlanView', () => {
  it('shows loading skeleton', () => {
    render(<PlanView plan={null} isLoading onOpenChat={vi.fn()} />);

    expect(screen.getByTestId('plan-skeleton')).toBeInTheDocument();
  });

  it('renders empty state when there is no active plan', () => {
    const onOpenChat = vi.fn();
    render(<PlanView plan={null} isLoading={false} onOpenChat={onOpenChat} />);

    expect(screen.getByText('plan.empty.title')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'plan.empty.cta' }));
    expect(onOpenChat).toHaveBeenCalledTimes(1);
  });

  it('renders plan sections for active plan', () => {
    render(<PlanView plan={mockPlan} isLoading={false} onOpenChat={vi.fn()} />);

    expect(screen.getByText('plan.sections.time_window')).toBeInTheDocument();
    expect(screen.getByText('01/04/2026 - 01/06/2026')).toBeInTheDocument();
    expect(screen.getByText('Plano Central')).toBeInTheDocument();
    expect(screen.getByText('plan.sections.mission_today')).toBeInTheDocument();
    expect(screen.getByText('Treino A - 50min')).toBeInTheDocument();
    expect(screen.queryByText('plan.cards.ai_followup')).not.toBeInTheDocument();
    expect(screen.getByText('plan.sections.upcoming_days')).toBeInTheDocument();
    expect(screen.getByText('Ter')).toBeInTheDocument();
    expect(screen.getByText('Supino Reto - 4x6-8 (RPE 8)')).toBeInTheDocument();
    expect(screen.getByText('plan.sections.latest_checkpoint')).toBeInTheDocument();
    expect(screen.queryByText('plan.sections.status')).not.toBeInTheDocument();
    expect(screen.getByText('Agachamento - 4x6-8 (RPE 8)')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'plan.actions.open_chat' })).not.toBeInTheDocument();
  });

  it('shows empty upcoming message when there are no upcoming days', () => {
    render(
      <PlanView
        plan={{ ...mockPlan, upcoming_days: [] }}
        isLoading={false}
        onOpenChat={vi.fn()}
      />
    );

    expect(screen.getByText('plan.upcoming.empty')).toBeInTheDocument();
  });
});
