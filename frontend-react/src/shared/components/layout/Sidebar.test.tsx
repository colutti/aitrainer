import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { useAuthStore, type AuthStore } from '../../hooks/useAuth';

import { Sidebar } from './Sidebar';

// Mock useAuthStore
vi.mock('../../hooks/useAuth', () => ({
  useAuthStore: vi.fn(),
}));

describe('Sidebar', () => {
  it('should render basic navigation links', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      isAdmin: false,
      logout: vi.fn(),
    } as AuthStore);

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );

    expect(screen.getByText(/Home/i)).toBeInTheDocument();
    expect(screen.getByText(/Treinos/i)).toBeInTheDocument();
    expect(screen.getByText(/Nutrição/i)).toBeInTheDocument();
    expect(screen.getByText(/Corpo/i)).toBeInTheDocument();
  });

  it('should render Admin link only for admin users', () => {
    // Non-admin
    vi.mocked(useAuthStore).mockReturnValue({
      isAdmin: false,
      logout: vi.fn(),
    } as AuthStore);

    const { rerender } = render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );

    expect(screen.queryByText(/Painel Admin/i)).not.toBeInTheDocument();

    // Admin
    vi.mocked(useAuthStore).mockReturnValue({
      isAdmin: true,
      logout: vi.fn(),
    } as AuthStore);

    rerender(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );

    expect(screen.getByText(/Painel Admin/i)).toBeInTheDocument();
  });

  it('should call logout when logout button is clicked', () => {
    const logout = vi.fn();
    vi.mocked(useAuthStore).mockReturnValue({
      isAdmin: false,
      logout,
    } as AuthStore);

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );

    const logoutButton = screen.getByText(/Sair/i);
    logoutButton.click();

    expect(logout).toHaveBeenCalledTimes(1);
  });
});
