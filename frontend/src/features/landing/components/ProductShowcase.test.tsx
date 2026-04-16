import { describe, it, expect } from 'vitest';

import { render, screen } from '../../../shared/utils/test-utils';

import { ProductShowcase } from './ProductShowcase';

describe('ProductShowcase Component', () => {
  it('renders the dashboard as a real multi-widget control center', () => {
    render(<ProductShowcase />);

    expect(screen.getByText(/Sistema operacional da sua evolução/i)).toBeInTheDocument();
    expect(screen.getByText(/confiança metabólica/i)).toBeInTheDocument();
    expect(screen.getByText(/atividade recente/i)).toBeInTheDocument();
  });

  it('keeps chat preview bubble readable in monochrome theme', () => {
    render(<ProductShowcase />);

    expect(screen.getByTestId('landing-chat-user-bubble')).toHaveClass('text-[color:var(--color-text-primary)]');
    expect(screen.getByTestId('landing-chat-user-bubble')).not.toHaveClass('text-white');
  });
});
