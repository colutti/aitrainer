import { describe, it, expect } from 'vitest';

import { render, screen } from '../../../shared/utils/test-utils';

import { Counters } from './Counters';

describe('Counters Component', () => {
  it('should render platform stats', () => {
    render(<Counters />);
    expect(screen.getByText(/Treinadores/i)).toBeInTheDocument();
    expect(screen.getByText(/Integrações/i)).toBeInTheDocument();
  });
});
