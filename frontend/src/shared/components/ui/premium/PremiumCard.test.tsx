import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { PremiumCard } from './PremiumCard';

describe('PremiumCard', () => {
  it('renders children correctly', () => {
    render(<PremiumCard>Test Content</PremiumCard>);
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('renders cards with the shared surface classes', () => {
    render(<PremiumCard data-testid="premium-card">Content</PremiumCard>);
    const card = screen.getByTestId('premium-card');

    expect(card).toHaveClass('bg-[color:var(--color-surface-container)]');
    expect(card).toHaveClass('border-[color:var(--color-outline-variant)]');
    expect(card).toHaveClass('rounded-[var(--radius-lg)]');
  });

  it('keeps hover styling opt-in by prop and within the shared surface tiers', () => {
    const { rerender } = render(<PremiumCard data-testid="premium-card">Content</PremiumCard>);
    const card = screen.getByTestId('premium-card');

    expect(card).toHaveClass('hover:bg-[color:var(--color-surface-container-high)]');

    rerender(
      <PremiumCard data-testid="premium-card" withHover={false}>
        Content
      </PremiumCard>
    );
    expect(screen.getByTestId('premium-card')).not.toHaveClass('hover:bg-[color:var(--color-surface-container-high)]');
  });

  it('merges custom className correctly', () => {
    render(<PremiumCard className="custom-class" data-testid="premium-card">Content</PremiumCard>);
    const card = screen.getByTestId('premium-card');
    expect(card).toHaveClass('bg-[color:var(--color-surface-container)]');
    expect(card).toHaveClass('custom-class');
  });
});
