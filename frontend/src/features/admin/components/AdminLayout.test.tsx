import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { AdminLayout } from './AdminLayout';

describe('AdminLayout', () => {
  it('should render navigation tabs', () => {
    render(
      <MemoryRouter>
        <AdminLayout />
      </MemoryRouter>
    );

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Usuários')).toBeInTheDocument();
    expect(screen.getByText('Logs')).toBeInTheDocument();
    expect(screen.getByText('Prompts')).toBeInTheDocument();
  });
});
