import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import type { PRRecord } from '../../../shared/types/dashboard';

import { WidgetRecentPRs } from './WidgetRecentPRs';

describe('WidgetRecentPRs', () => {
  const mockPRs: PRRecord[] = [
    {
      id: '1',
      exercise: 'Agachamento',
      weight: 100,
      reps: 5,
      date: '2024-01-01',
      previous_weight: 90,
    },
    {
      id: '2',
      exercise: 'Supino',
      weight: 80,
      reps: 8,
      date: '2024-01-02',
    },
  ];

  it('should render with overlay if no PRs provided', () => {
    render(<WidgetRecentPRs prs={[]} />);
    expect(screen.getByText('Recordes Pessoais')).toBeInTheDocument();
    expect(screen.getByText('Nenhum recorde ainda')).toBeInTheDocument();
  });

  it('should render list of PRs', () => {
    render(<WidgetRecentPRs prs={mockPRs} />);
    
    expect(screen.getByText('Agachamento')).toBeInTheDocument();
    expect(screen.getByText('Supino')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
    expect(screen.getByText('80')).toBeInTheDocument();
  });

  it('should show weight increase if previous_weight exists', () => {
    render(<WidgetRecentPRs prs={mockPRs} />);
    expect(screen.getByText('+10.00kg')).toBeInTheDocument();
  });
});
