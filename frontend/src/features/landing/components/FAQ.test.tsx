import { describe, it, expect } from 'vitest';

import { render, screen } from '../../../shared/utils/test-utils';

import { FAQ } from './FAQ';

describe('FAQ Component', () => {
  it('should render FAQ items', () => {
    render(<FAQ />);
    
    // We check for some translation keys that should be rendered by our real pt-BR.json
    expect(screen.getByText(/FAQ/i)).toBeInTheDocument();
    expect(screen.getByText(/Como funciona a memória AI/i)).toBeInTheDocument();
  });
});
