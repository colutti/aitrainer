import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { PremiumCard } from './PremiumCard';

describe('PremiumCard', () => {
  it('renders children correctly', () => {
    render(<PremiumCard>Test Content</PremiumCard>);
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('applies the glassmorphism utility classes', () => {
    render(<PremiumCard data-testid="premium-card">Content</PremiumCard>);
    const card = screen.getByTestId('premium-card');
    
    // Validamos as novas classes utilitárias semânticas
    expect(card).toHaveClass('glass-card');
    expect(card).toHaveClass('glass-card-hover');
  });

  it('merges custom className correctly', () => {
    render(<PremiumCard className="custom-class" data-testid="premium-card">Content</PremiumCard>);
    const card = screen.getByTestId('premium-card');
    expect(card).toHaveClass('glass-card');
    expect(card).toHaveClass('custom-class');
  });
});
