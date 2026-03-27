import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockLogin = vi.fn();
const mockNavigate = vi.fn();

vi.mock('../../shared/hooks/useAdminAuth', () => ({
  useAdminLogin: () => mockLogin,
  useAdminIsLoading: () => false,
  useAdminLoginError: () => null,
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>(
    'react-router-dom'
  );
  return { ...actual, useNavigate: () => mockNavigate };
});

import { LoginPage } from './LoginPage';

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLogin.mockResolvedValue(undefined);
  });

  it('submits credentials and navigates to the dashboard', async () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByPlaceholderText('admin@fityq.com'), {
      target: { value: 'admin@fityq.com' },
    });
    fireEvent.change(screen.getByPlaceholderText('••••••••'), {
      target: { value: 'secret' },
    });
    fireEvent.click(
      screen.getByRole('button', { name: /entrar no painel/i })
    );

    await waitFor(() =>
      expect(mockLogin).toHaveBeenCalledWith('admin@fityq.com', 'secret')
    );
    expect(mockNavigate).toHaveBeenCalledWith('/');
  });
});
