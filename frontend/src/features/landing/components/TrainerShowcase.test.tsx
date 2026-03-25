import { describe, it, expect } from 'vitest';

import { render, screen } from '../../../shared/utils/test-utils';

import { TrainerShowcase } from './TrainerShowcase';

describe('TrainerShowcase Component', () => {
  it('should render trainer profiles', () => {
    render(<TrainerShowcase />);
    expect(screen.getByText(/Conheça seu Mentor/i)).toBeInTheDocument();
    expect(screen.getByText('Atlas Prime')).toBeInTheDocument();
    expect(screen.getByText('Luna Stardust')).toBeInTheDocument();
  });
});
