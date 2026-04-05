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
});
