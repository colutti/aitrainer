import { describe, expect, it, vi } from 'vitest';

import { render, screen } from '../../utils/test-utils';

import { PlanCard } from './PlanCard';

describe('PlanCard', () => {
  it('renders plan content and action button', () => {
    render(
      <PlanCard
        plan={{
          id: 'pro',
          name: 'Pro',
          subtitle: 'A experiência completa com dados, fotos e automações.',
          priceLabel: '$9.99/mo',
          features: ['300 mensagens por mês', 'Fotos no chat'],
          badge: 'Recomendado',
          highlight: true,
        }}
        context="marketing"
        actionLabel="Assinar Pro"
        onAction={vi.fn()}
      />
    );

    expect(screen.getByText('Pro')).toBeInTheDocument();
    expect(screen.getByText('300 mensagens por mês')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Assinar Pro' })).toBeInTheDocument();
  });
});
