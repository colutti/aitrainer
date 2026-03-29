import { describe, it, expect } from 'vitest';

import { render, screen } from '../../../shared/utils/test-utils';

import { Footer } from './Footer';

describe('Footer Component', () => {
  it('should render footer content', () => {
    render(<Footer />);
    expect(screen.getByText(/Todos os direitos reservados/i)).toBeInTheDocument();
  });

  it('renders localized footer links', () => {
    render(<Footer />);

    expect(screen.getByRole('link', { name: /termos/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /privacidade/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /contato/i })).toBeInTheDocument();
  });
});
