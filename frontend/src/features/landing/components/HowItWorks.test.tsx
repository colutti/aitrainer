import { describe, it, expect } from 'vitest';

import { render, screen } from '../../../shared/utils/test-utils';

import { HowItWorks } from './HowItWorks';

describe('HowItWorks Component', () => {
  it('should render step by step guide', () => {
    render(<HowItWorks />);
    expect(screen.getByText(/Como Funciona/i)).toBeInTheDocument();
    expect(screen.getByText(/Conecte/i)).toBeInTheDocument();
  });
});
