import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { useAuthStore, type AuthStore } from '../../hooks/useAuth';

import { AuthGuard } from './AuthGuard';

// Mock useAuthStore
vi.mock('../../hooks/useAuth', () => ({
  useAuthStore: vi.fn(),
}));

describe('AuthGuard', () => {
  it('should render children when not authenticated', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
    } as AuthStore);

    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route
            path="/login"
            element={
              <AuthGuard>
                <div data-testid="login-content">Login Page</div>
              </AuthGuard>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByTestId('login-content')).toBeInTheDocument();
  });

  it('should redirect to dashboard when already authenticated', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
    } as AuthStore);

    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route
            path="/login"
            element={
              <AuthGuard>
                <div data-testid="login-content">Login Page</div>
              </AuthGuard>
            }
          />
          <Route path="/dashboard" element={<div data-testid="dashboard-page">Dashboard</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.queryByTestId('login-content')).not.toBeInTheDocument();
    expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
  });
});
