import { describe, it, expect } from 'vitest';

import { render, screen } from '../../../shared/utils/test-utils';

import { HowItWorks } from './HowItWorks';

describe('HowItWorks Component', () => {
  it('renders the practical three-step flow', () => {
    render(<HowItWorks />);

    expect(screen.getByText(/Como funciona na prática/i)).toBeInTheDocument();
    expect(screen.getByText(/Seus dados entram/i)).toBeInTheDocument();
    expect(screen.getByText(/O sistema organiza sinais e tendências/i)).toBeInTheDocument();
  });
});
