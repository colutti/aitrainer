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
      isAuthenticated: true,
      isLoading: false,
      userInfo: { email: 'user@example.com', is_admin: false, id: '1', name: 'User' },
      isAdmin: false,
      logout: vi.fn(),
    } as unknown as AuthStore);

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );

    expect(screen.getByText(/Início/i)).toBeInTheDocument();
    expect(screen.getByText(/Treinador/i)).toBeInTheDocument();
    expect(screen.getByText(/Meus Treinos/i)).toBeInTheDocument();
    expect(screen.getByText(/Peso e Corpo/i)).toBeInTheDocument();
    expect(screen.getByText(/Dieta e Macros/i)).toBeInTheDocument();
  });

  it('should render settings navigation links in bottom section', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      userInfo: { email: 'user@example.com', is_admin: false, id: '1', name: 'User' },
      isAdmin: false,
      logout: vi.fn(),
    } as unknown as AuthStore);

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );

    expect(screen.getByText(/Configurações/i)).toBeInTheDocument();
  });

  it('should render Admin link only for admin users', () => {
    // Non-admin
    vi.mocked(useAuthStore).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      userInfo: { email: 'user@example.com', is_admin: false, id: '1', name: 'User' },
      isAdmin: false,
      logout: vi.fn(),
    } as unknown as AuthStore);

    const { rerender } = render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );

    expect(screen.queryByText(/Painel Admin/i)).not.toBeInTheDocument();

    // Admin
    vi.mocked(useAuthStore).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      userInfo: { email: 'admin@example.com', is_admin: true, id: '2', name: 'Admin' },
      isAdmin: true,
      logout: vi.fn(),
    } as unknown as AuthStore);

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
      isAuthenticated: true,
      isLoading: false,
      userInfo: { email: 'user@example.com', is_admin: false, id: '1', name: 'User' },
      isAdmin: false,
      logout,
    } as unknown as AuthStore);

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

