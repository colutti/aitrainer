import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { useAuthStore, type AuthStore } from '../../hooks/useAuth';

import { AuthGuard } from './AuthGuard';

// Mock useAuthStore
vi.mock('../../hooks/useAuth', () => ({
  useAuthStore: vi.fn(),
}));

const createAuthStoreMock = (overrides: Partial<AuthStore> = {}): AuthStore => ({
  isAuthenticated: false,
  userInfo: null,
  isAdmin: false,
  isLoading: false,
  login: vi.fn(async () => {}),
  register: vi.fn(async () => {}),
  socialLogin: vi.fn(async () => {}),
  requestPasswordReset: vi.fn(async () => {}),
  logout: vi.fn(),
  loadUserInfo: vi.fn(async () => ({
    email: 'test@example.com',
    name: 'Test User',
    is_admin: false,
    onboarding_completed: true,
    has_stripe_customer: false,
  })),
  getToken: vi.fn(() => null),
  init: vi.fn(async () => {}),
  refreshToken: vi.fn(async () => false),
  ...overrides,
});

describe('AuthGuard', () => {
  it('should render children when not authenticated', () => {
    vi.mocked(useAuthStore).mockReturnValue(createAuthStoreMock({
      isAuthenticated: false,
      isLoading: false,
      userInfo: null,
      isAdmin: false,
      logout: vi.fn(),
    }));

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
    vi.mocked(useAuthStore).mockReturnValue(createAuthStoreMock({
      isAuthenticated: true,
      isLoading: false,
      userInfo: { onboarding_completed: true } as any,
      isAdmin: false,
      logout: vi.fn(),
    }));

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

  it('should redirect authenticated onboarding-incomplete users to onboarding', () => {
    vi.mocked(useAuthStore).mockReturnValue(createAuthStoreMock({
      isAuthenticated: true,
      isLoading: false,
      userInfo: { onboarding_completed: false } as any,
      isAdmin: false,
      logout: vi.fn(),
    }));

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
          <Route path="/onboarding" element={<div data-testid="onboarding-page">Onboarding</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.queryByTestId('login-content')).not.toBeInTheDocument();
    expect(screen.getByTestId('onboarding-page')).toBeInTheDocument();
  });

  it('should render children when auth state is inconsistent (authenticated without user info)', () => {
    vi.mocked(useAuthStore).mockReturnValue(createAuthStoreMock({
      isAuthenticated: true,
      isLoading: false,
      userInfo: null,
      isAdmin: false,
      logout: vi.fn(),
    }));

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

    expect(screen.getByTestId('login-content')).toBeInTheDocument();
    expect(screen.queryByTestId('dashboard-page')).not.toBeInTheDocument();
  });
});
