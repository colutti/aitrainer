import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { WidgetStreak } from './WidgetStreak';

describe('WidgetStreak', () => {
  it('should render zero streak by default', () => {
    render(<WidgetStreak />);
    expect(screen.getByText('0')).toBeInTheDocument();
    expect(screen.queryByText('d')).not.toBeInTheDocument();
  });

  it('should render weeks and days when provided', () => {
    render(<WidgetStreak currentWeeks={5} currentDays={3} />);
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('w')).toBeInTheDocument();
    expect(screen.getByText('d')).toBeInTheDocument();
  });

  it('should only render weeks if currentDays is 0', () => {
    render(<WidgetStreak currentWeeks={4} currentDays={0} />);
    expect(screen.getByText('4')).toBeInTheDocument();
    expect(screen.queryByText('d')).not.toBeInTheDocument();
  });
});
