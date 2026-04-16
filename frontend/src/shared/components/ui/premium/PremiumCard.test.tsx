import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { PremiumCard } from './PremiumCard';

describe('PremiumCard', () => {
  it('renders children correctly', () => {
    render(<PremiumCard>Test Content</PremiumCard>);
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('uses solid surface utility classes instead of glassmorphism', () => {
    render(<PremiumCard data-testid="premium-card">Content</PremiumCard>);
    const card = screen.getByTestId('premium-card');

    expect(card).toHaveClass('surface-card');
    expect(card).toHaveClass('surface-card-hover');
    expect(card).not.toHaveClass('glass-card');
    expect(card).not.toHaveClass('glass-card-hover');
  });

  it('merges custom className correctly', () => {
    render(<PremiumCard className="custom-class" data-testid="premium-card">Content</PremiumCard>);
    const card = screen.getByTestId('premium-card');
    expect(card).toHaveClass('surface-card');
    expect(card).toHaveClass('custom-class');
  });
});
