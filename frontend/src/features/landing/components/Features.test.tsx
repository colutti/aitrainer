import { describe, it, expect } from 'vitest';

import { render, screen } from '../../../shared/utils/test-utils';

import { Features } from './Features';

describe('Features Component', () => {
  it('should render features section', () => {
    render(<Features />);
    expect(screen.getByText(/Diferenciais/i)).toBeInTheDocument();
    expect(screen.getByText(/Análise Metabólica/i)).toBeInTheDocument();
  });
});
