import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { useAuthStore } from '../../shared/hooks/useAuth';
import { useNotificationStore } from '../../shared/hooks/useNotification';

import LoginPage from './LoginPage';

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
    register: vi.fn(),
    socialLogin: vi.fn(),
    requestPasswordReset: vi.fn(),
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

    expect(screen.getByPlaceholderText(/exemplo@email\.com/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/••••••••/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Entrar$/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Entrar com Google/i })).toBeInTheDocument();
  });

  it('should not use white background in auth tab active indicator', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    const activeIndicator = screen.getByTestId('auth-tab-indicator');
    expect(activeIndicator.className).not.toContain('bg-white');
  });

  it('should not render the Deep Space Premium badge', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    expect(screen.queryByText(/Deep Space Premium/i)).not.toBeInTheDocument();
  });

  it('should show validation errors for empty fields', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    await user.click(screen.getByRole('button', { name: /^Entrar$/i }));

    await waitFor(() => {
      expect(screen.getByText(/E-mail inválido/i)).toBeInTheDocument();
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

    await user.type(screen.getByPlaceholderText(/exemplo@email\.com/i), 'test@example.com');
    await user.type(screen.getByPlaceholderText(/••••••••/i), 'password123');

    await user.click(screen.getByRole('button', { name: /^Entrar$/i }));

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith('test@example.com', 'password123');
    });
  });

  it('should render register form from query param and call register action', async () => {
    const user = userEvent.setup();
    const registerMock = vi.fn().mockResolvedValue(undefined);

    vi.mocked(useAuthStore).mockImplementation((selector?: unknown) => {
      const state = { ...mockAuth, register: registerMock };
      if (typeof selector === 'function') {
        return (selector as (s: typeof state) => unknown)(state);
      }
      return state;
    });

    render(
      <MemoryRouter initialEntries={['/login?mode=register']}>
        <LoginPage />
      </MemoryRouter>
    );

    await user.type(screen.getByPlaceholderText(/Seu nome/i), 'Fresh User');
    await user.type(screen.getByPlaceholderText(/exemplo@email\.com/i), 'fresh@example.com');
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    await user.type(passwordInputs[0] as HTMLInputElement, 'password123');
    await user.type(passwordInputs[1] as HTMLInputElement, 'password123');

    await user.click(screen.getByRole('button', { name: /Criar Conta/i }));

    await waitFor(() => {
      expect(registerMock).toHaveBeenCalledWith('Fresh User', 'fresh@example.com', 'password123');
    });
  });

  it('should show duplicate email guidance when register fails with existing user', async () => {
    const user = userEvent.setup();
    const registerMock = vi.fn().mockRejectedValue(Object.assign(new Error('Duplicate'), {
      code: 'auth/email-already-in-use',
    }));

    vi.mocked(useAuthStore).mockImplementation((selector?: unknown) => {
      const state = { ...mockAuth, register: registerMock };
      if (typeof selector === 'function') {
        return (selector as (s: typeof state) => unknown)(state);
      }
      return state;
    });

    render(
      <MemoryRouter initialEntries={['/login?mode=register']}>
        <LoginPage />
      </MemoryRouter>
    );

    await user.type(screen.getByPlaceholderText(/Seu nome/i), 'Fresh User');
    await user.type(screen.getByPlaceholderText(/exemplo@email\.com/i), 'fresh@example.com');
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    await user.type(passwordInputs[0] as HTMLInputElement, 'password123');
    await user.type(passwordInputs[1] as HTMLInputElement, 'password123');
    await user.click(screen.getByRole('button', { name: /Criar Conta/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/Este e-mail já está cadastrado/i)
      ).toBeInTheDocument();
    });
  });

  it('should show error notification when login fails', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const user = userEvent.setup();
    const loginMock = vi.fn().mockRejectedValue(new Error('Invalid credentials'));

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

    await user.type(screen.getByPlaceholderText(/exemplo@email\.com/i), 'test@example.com');
    await user.type(screen.getByPlaceholderText(/••••••••/i), 'password123');

    await user.click(screen.getByRole('button', { name: /^Entrar$/i }));

    await waitFor(() => {
      expect(screen.getByText(/E-mail ou senha incorreto/i)).toBeInTheDocument();
    });
    consoleSpy.mockRestore();
  });

  it('should call social login when clicking Google button', async () => {
    const user = userEvent.setup();
    const socialLoginMock = vi.fn().mockResolvedValue(undefined);

    vi.mocked(useAuthStore).mockImplementation((selector?: unknown) => {
      const state = { ...mockAuth, socialLogin: socialLoginMock };
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

    await user.click(screen.getByRole('button', { name: /Entrar com Google/i }));

    await waitFor(() => {
      expect(socialLoginMock).toHaveBeenCalledWith('google');
    });
  });

  it('should show loading only on submit button when email login is pending', async () => {
    const user = userEvent.setup();
    const loginMock = vi.fn(() => new Promise<void>(() => {}));

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

    await user.type(screen.getByPlaceholderText(/exemplo@email\.com/i), 'test@example.com');
    await user.type(screen.getByPlaceholderText(/••••••••/i), 'password123');
    await user.click(screen.getByRole('button', { name: /^Entrar$/i }));

    await waitFor(() => {
      const emailLoginButton = screen.getByRole('button', { name: /^Entrar$/i });
      const googleLoginButton = screen.getByRole('button', { name: /Entrar com Google/i });

      expect(emailLoginButton.querySelector('.animate-spin')).toBeInTheDocument();
      expect(googleLoginButton.querySelector('.animate-spin')).not.toBeInTheDocument();
    });
  });

  it('should show error when forgot password is clicked without email', async () => {
    const user = userEvent.setup();
    const requestPasswordResetMock = vi.fn().mockResolvedValue(undefined);

    vi.mocked(useAuthStore).mockImplementation((selector?: unknown) => {
      const state = { ...mockAuth, requestPasswordReset: requestPasswordResetMock };
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

    await user.click(screen.getByRole('button', { name: /Esqueci a senha/i }));

    await waitFor(() => {
      expect(screen.getByText(/Informe seu e-mail para recuperar a senha/i)).toBeInTheDocument();
    });
    expect(requestPasswordResetMock).not.toHaveBeenCalled();
  });

  it('should request password reset and show generic feedback', async () => {
    const user = userEvent.setup();
    const requestPasswordResetMock = vi.fn().mockResolvedValue(undefined);

    vi.mocked(useAuthStore).mockImplementation((selector?: unknown) => {
      const state = { ...mockAuth, requestPasswordReset: requestPasswordResetMock };
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

    await user.type(screen.getByTestId('login-email'), 'person@example.com');
    await user.click(screen.getByRole('button', { name: /Esqueci a senha/i }));

    await waitFor(() => {
      expect(requestPasswordResetMock).toHaveBeenCalledWith('person@example.com');
      expect(screen.getByText(/Se o e-mail estiver cadastrado/i)).toBeInTheDocument();
    });
  });

  it('should show service error when reset email request fails for operational reasons', async () => {
    const user = userEvent.setup();
    const requestPasswordResetMock = vi.fn().mockRejectedValue(
      Object.assign(new Error('service unavailable'), { code: 'auth/network-request-failed' })
    );

    vi.mocked(useAuthStore).mockImplementation((selector?: unknown) => {
      const state = { ...mockAuth, requestPasswordReset: requestPasswordResetMock };
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

    await user.type(screen.getByTestId('login-email'), 'person@example.com');
    await user.click(screen.getByRole('button', { name: /Esqueci a senha/i }));

    await waitFor(() => {
      expect(requestPasswordResetMock).toHaveBeenCalledWith('person@example.com');
      expect(screen.getByText(/Não foi possível enviar o e-mail de recuperação agora/i)).toBeInTheDocument();
    });
    expect(screen.queryByText(/Se o e-mail estiver cadastrado/i)).not.toBeInTheDocument();
  });
});
