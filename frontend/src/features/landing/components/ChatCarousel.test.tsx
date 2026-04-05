import { describe, it, expect } from 'vitest';

import { render, screen } from '../../../shared/utils/test-utils';

import { ChatCarousel } from './ChatCarousel';

describe('ChatCarousel Component', () => {
  it('renders the product-proof demo section', () => {
    render(<ChatCarousel />);

    expect(screen.getByText(/Veja como o FityQ trabalha no seu dia a dia/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Sua rotina/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/O sistema entende/i)).toBeInTheDocument();
    expect(screen.getByText(/Seu treinador orienta/i)).toBeInTheDocument();
    expect(screen.getByText(/Uma semana comum, tratada com mais inteligência/i)).toBeInTheDocument();
  });
});
