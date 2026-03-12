import { render, screen } from '@testing-library/react';
import { Home } from 'lucide-react'; // Example icon
import { describe, expect, it } from 'vitest';

import { MacroCard } from './MacroCard';

describe('MacroCard', () => {
  const defaultProps = {
    label: 'Protein',
    value: 150,
    unit: 'g',
    percent: 75,
    color: 'primary' as const,
    icon: <Home data-testid="icon" />,
  };

  it('should render correct content', () => {
     render(<MacroCard {...defaultProps} />);
     
     expect(screen.getByText('Protein')).toBeInTheDocument();
     expect(screen.getByText(/150/)).toBeInTheDocument();
     expect(screen.getByText('g')).toBeInTheDocument();
     expect(screen.getByTestId('icon')).toBeInTheDocument();
  });

  it('should render progress percentage limited to 100%', () => {
    render(<MacroCard {...defaultProps} percent={120} />);
    
    // The component logic is Math.min(percent, 100).
    // So it should show 100%.
    expect(screen.getByText('100%')).toBeInTheDocument();

    // Check width style if needed, but text assertion is good enough for visible output.
  });

  it('should render progress below 100%', () => {
    render(<MacroCard {...defaultProps} percent={50} />);
    expect(screen.getByText('50%')).toBeInTheDocument();
  });
});
