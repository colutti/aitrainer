import { describe, it, expect } from 'vitest';

import { render, screen } from '../../../shared/utils/test-utils';

import { ProductShowcase } from './ProductShowcase';

describe('ProductShowcase Component', () => {
  it('should render product features', () => {
    render(<ProductShowcase />);
    expect(screen.getByText(/Tudo em um só lugar/i)).toBeInTheDocument();
  });
});
