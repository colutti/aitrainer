import { describe, it, expect } from 'vitest';

import { render, screen } from '../../../shared/utils/test-utils';

import { Features } from './Features';

describe('Features Component', () => {
  it('only shows real differentiators', () => {
    render(<Features />);

    expect(screen.getByText(/Memória que aprende com sua rotina/i)).toBeInTheDocument();
    expect(screen.queryByText(/Vis[aã]o Computacional/i)).not.toBeInTheDocument();
  });
});
