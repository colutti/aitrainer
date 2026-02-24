import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { useAuthStore, type AuthStore } from '../../hooks/useAuth';

import { ProtectedRoute } from './ProtectedRoute';

// Mock useAuthStore
vi.mock('../../hooks/useAuth', () => ({
  useAuthStore: vi.fn(),
}));

describe('ProtectedRoute', () => {
  it('should render children when authenticated', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      isAuthenticated: true,
      isAdmin: false,
      isLoading: false,
    } as AuthStore);

    render(
      <MemoryRouter initialEntries={['/protected']}>
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute>
                <div data-testid="protected-content">Protected</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
  });

  it('should redirect to landing when not authenticated', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      isAuthenticated: false,
      isAdmin: false,
      isLoading: false,
    } as AuthStore);

    render(
      <MemoryRouter initialEntries={['/protected']}>
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute>
                <div data-testid="protected-content">Protected</div>
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<div data-testid="landing-page">Landing</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    expect(screen.getByTestId('landing-page')).toBeInTheDocument();
  });

  it('should redirect to dashboard when admin is required but user is not admin', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      isAuthenticated: true,
      isAdmin: false,
      isLoading: false,
    } as AuthStore);

    render(
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route
            path="/admin"
            element={
              <ProtectedRoute requireAdmin>
                <div data-testid="admin-content">Admin Only</div>
              </ProtectedRoute>
            }
          />
          <Route path="/dashboard" element={<div data-testid="dashboard-page">Dashboard</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.queryByTestId('admin-content')).not.toBeInTheDocument();
    expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
  });

  it('should render children when admin is required and user is admin', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      isAuthenticated: true,
      isAdmin: true,
      isLoading: false,
    } as AuthStore);

    render(
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route
            path="/admin"
            element={
              <ProtectedRoute requireAdmin>
                <div data-testid="admin-content">Admin Only</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByTestId('admin-content')).toBeInTheDocument();
  });

  it('should render nothing (or skeleton) while loading', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      isAuthenticated: false,
      isAdmin: false,
      isLoading: true,
    } as AuthStore);

    render(
      <MemoryRouter initialEntries={['/protected']}>
        <ProtectedRoute>
          <div data-testid="protected-content">Protected</div>
        </ProtectedRoute>
      </MemoryRouter>
    );

    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });
});
