import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { render } from '../../shared/utils/test-utils';

import ResetPasswordPage from './ResetPasswordPage';

const confirmPasswordResetMock = vi.fn();
const verifyPasswordResetCodeMock = vi.fn();

vi.mock('./firebase', () => ({
  auth: {},
}));

vi.mock('firebase/auth', () => ({
  confirmPasswordReset: (...args: unknown[]) => confirmPasswordResetMock(...args),
  verifyPasswordResetCode: (...args: unknown[]) => verifyPasswordResetCodeMock(...args),
}));

describe('ResetPasswordPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    verifyPasswordResetCodeMock.mockResolvedValue('person@example.com');
    confirmPasswordResetMock.mockResolvedValue(undefined);
  });

  it('blocks weak passwords and does not submit', async () => {
    const user = userEvent.setup();
    render(<ResetPasswordPage />, { route: '/auth/action?mode=resetPassword&oobCode=test-oob' });

    await waitFor(() => {
      expect(verifyPasswordResetCodeMock).toHaveBeenCalled();
    });

    await user.type(screen.getByLabelText(/^Nova senha$/i), 'abc');
    await user.type(screen.getByLabelText(/^Confirmar nova senha$/i), 'abc');
    await user.click(screen.getByRole('button', { name: /Salvar nova senha/i }));

    await waitFor(() => {
      expect(screen.getByText(/A senha deve conter no mínimo 8 caracteres/i)).toBeInTheDocument();
    });
    expect(confirmPasswordResetMock).not.toHaveBeenCalled();
  });

  it('submits when password is strong', async () => {
    const user = userEvent.setup();
    render(<ResetPasswordPage />, { route: '/auth/action?mode=resetPassword&oobCode=test-oob' });

    await waitFor(() => {
      expect(verifyPasswordResetCodeMock).toHaveBeenCalled();
    });

    await user.type(screen.getByLabelText(/^Nova senha$/i), 'FityQ!2026');
    await user.type(screen.getByLabelText(/^Confirmar nova senha$/i), 'FityQ!2026');
    await user.click(screen.getByRole('button', { name: /Salvar nova senha/i }));

    await waitFor(() => {
      expect(confirmPasswordResetMock).toHaveBeenCalledWith(expect.anything(), 'test-oob', 'FityQ!2026');
    });
  });

  it('shows error when confirmation does not match password', async () => {
    const user = userEvent.setup();
    render(<ResetPasswordPage />, { route: '/auth/action?mode=resetPassword&oobCode=test-oob' });

    await waitFor(() => {
      expect(verifyPasswordResetCodeMock).toHaveBeenCalled();
    });

    await user.type(screen.getByLabelText(/^Nova senha$/i), 'FityQ!2026');
    await user.type(screen.getByLabelText(/^Confirmar nova senha$/i), 'FityQ!2027');
    await user.click(screen.getByRole('button', { name: /Salvar nova senha/i }));

    await waitFor(() => {
      expect(screen.getByText(/As senhas não coincidem\./i)).toBeInTheDocument();
    });
    expect(confirmPasswordResetMock).not.toHaveBeenCalled();
  });

  it('shows invalid link message when mode is not resetPassword', async () => {
    render(<ResetPasswordPage />, { route: '/auth/action?mode=verifyEmail&oobCode=test-oob' });

    await waitFor(() => {
      expect(screen.getByText(/Link inválido ou expirado/i)).toBeInTheDocument();
    });
    expect(verifyPasswordResetCodeMock).not.toHaveBeenCalled();
    expect(confirmPasswordResetMock).not.toHaveBeenCalled();
  });
});
