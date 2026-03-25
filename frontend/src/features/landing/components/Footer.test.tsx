import { describe, it, expect } from 'vitest';

import { render, screen } from '../../../shared/utils/test-utils';

import { Footer } from './Footer';

describe('Footer Component', () => {
  it('should render footer content', () => {
    render(<Footer />);
    expect(screen.getByText(/Todos os direitos reservados/i)).toBeInTheDocument();
  });
});
