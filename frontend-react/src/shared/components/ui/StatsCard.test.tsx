import { render, screen } from '@testing-library/react';
import { Activity } from 'lucide-react';
import { describe, expect, it } from 'vitest';

import { StatsCard } from './StatsCard';

describe('StatsCard', () => {
  it('should render title and value', () => {
    render(
      <StatsCard
        title="Total Weight"
        value="80 kg"
        icon={<Activity size={24} />}
      />
    );

    expect(screen.getByText('Total Weight')).toBeInTheDocument();
    expect(screen.getByText('80 kg')).toBeInTheDocument();
  });

  it('should render subtitle when provided', () => {
    render(
      <StatsCard
        title="Weight"
        value="80 kg"
        subtitle="Last month: 82 kg"
        icon={<Activity size={24} />}
      />
    );

    expect(screen.getByText('Last month: 82 kg')).toBeInTheDocument();
  });

  it('should render trend information', () => {
    render(
      <StatsCard
        title="Weight"
        value="80 kg"
        icon={<Activity size={24} />}
        trend="down"
        trendValue="-2 kg"
      />
    );

    expect(screen.getByText('down')).toBeInTheDocument();
    expect(screen.getByText('-2 kg')).toBeInTheDocument();
  });

  it('should apply variant styles', () => {
    const { container } = render(
      <StatsCard
        title="Weight"
        value="80 kg"
        icon={<Activity size={24} data-testid="icon-wrapper" />}
        variant="orange"
      />
    );

    // The icon wrapper div should have the orange gradient classes
    const iconContainer = container.querySelector('.text-orange-500');
    expect(iconContainer).toBeInTheDocument();
  });
});
