import { describe, it, expect } from 'vitest';

import { render, screen } from '../../../shared/utils/test-utils';

import { ComparisonTable } from './ComparisonTable';

describe('ComparisonTable Component', () => {
  it('should render comparison features', () => {
    render(<ComparisonTable />);
    expect(screen.getByText(/Comparativo de Planos/i)).toBeInTheDocument();
    expect(screen.getByText(/Personalização/i)).toBeInTheDocument();
  });
});
