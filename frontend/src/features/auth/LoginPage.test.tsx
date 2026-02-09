import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { useAuthStore } from '../../shared/hooks/useAuth';
import { useNotificationStore } from '../../shared/hooks/useNotification';

import { LoginPage } from './LoginPage';

// Mock stores
vi.mock('../../shared/hooks/useAuth', () => ({
  useAuthStore: vi.fn(),
}));

vi.mock('../../shared/hooks/useNotification', () => ({
  useNotificationStore: vi.fn(),
}));

describe('LoginPage', () => {
  const mockNotification = {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  };

  const mockAuth = {
    login: vi.fn(),
    logout: vi.fn(),
    initialize: vi.fn(),
    isAuthenticated: false,
    isAdmin: false,
    isLoading: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Default mock for useNotificationStore
    vi.mocked(useNotificationStore).mockImplementation((selector?: unknown) => {
      if (typeof selector === 'function') {
        return (selector as (s: typeof mockNotification) => unknown)(mockNotification);
      }
      return mockNotification;
    });

    // Default mock for useAuthStore
    vi.mocked(useAuthStore).mockImplementation((selector?: unknown) => {
      if (typeof selector === 'function') {
        return (selector as (s: typeof mockAuth) => unknown)(mockAuth);
      }
      return mockAuth;
    });
  });

  it('should render login form', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Senha/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Entrar/i })).toBeInTheDocument();
  });

  it('should show validation errors for empty fields', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    await user.click(screen.getByRole('button', { name: /Entrar/i }));

    await waitFor(() => {
      expect(screen.getByText(/Email inválido/i)).toBeInTheDocument();
      expect(screen.getByText(/A senha deve ter pelo menos 6 caracteres/i)).toBeInTheDocument();
    });
  });

  it('should call login store action on valid submit', async () => {
    const user = userEvent.setup();
    const loginMock = vi.fn().mockResolvedValue(undefined);
    
    vi.mocked(useAuthStore).mockImplementation((selector?: unknown) => {
      const state = { ...mockAuth, login: loginMock };
      if (typeof selector === 'function') {
        return (selector as (s: typeof state) => unknown)(state);
      }
      return state;
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText(/Email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/Senha/i), 'password123');

    await user.click(screen.getByRole('button', { name: /Entrar/i }));

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith('test@example.com', 'password123');
    });
  });

  it('should show error notification when login fails', async () => {
    const user = userEvent.setup();
    const loginMock = vi.fn().mockRejectedValue(new Error('Invalid credentials'));
    const errorNotificationMock = vi.fn();

    vi.mocked(useAuthStore).mockImplementation((selector?: unknown) => {
      const state = { ...mockAuth, login: loginMock };
      if (typeof selector === 'function') {
        return (selector as (s: typeof state) => unknown)(state);
      }
      return state;
    });

    vi.mocked(useNotificationStore).mockImplementation((selector?: unknown) => {
      const state = { ...mockNotification, error: errorNotificationMock };
      if (typeof selector === 'function') {
        return (selector as (s: typeof state) => unknown)(state);
      }
      return state;
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText(/Email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/Senha/i), 'password123');

    await user.click(screen.getByRole('button', { name: /Entrar/i }));

    await waitFor(() => {
      expect(errorNotificationMock).toHaveBeenCalledWith(expect.stringContaining('Falha no login'));
    });
  });
});
