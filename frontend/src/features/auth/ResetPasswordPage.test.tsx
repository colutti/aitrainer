import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import ResetPasswordPage from './ResetPasswordPage';

const verifyPasswordResetCodeMock = vi.fn();
const confirmPasswordResetMock = vi.fn();

vi.mock('./firebase', () => ({
  auth: {},
}));

vi.mock('firebase/auth', () => ({
  verifyPasswordResetCode: (...args: unknown[]) => verifyPasswordResetCodeMock(...args),
  confirmPasswordReset: (...args: unknown[]) => confirmPasswordResetMock(...args),
}));

describe('ResetPasswordPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    verifyPasswordResetCodeMock.mockResolvedValue('user@example.com');
    confirmPasswordResetMock.mockResolvedValue(undefined);
  });

  it('shows invalid link message when oobCode is missing', async () => {
    render(
      <MemoryRouter initialEntries={['/reset-password']}>
        <ResetPasswordPage />
      </MemoryRouter>
    );

    expect(screen.getByText(/link inválido ou expirado/i)).toBeInTheDocument();
  });

  it('validates strong password policy before submit', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={['/reset-password?oobCode=valid-code']}>
        <ResetPasswordPage />
      </MemoryRouter>
    );

    const passwordInput = await screen.findByLabelText(/^Nova senha$/i);
    const confirmPasswordInput = await screen.findByLabelText(/^Confirmar nova senha$/i);

    await user.type(passwordInput, 'abc123');
    await user.type(confirmPasswordInput, 'abc123');
    await user.click(screen.getByRole('button', { name: /redefinir senha/i }));

    await waitFor(() => {
      expect(screen.getByText(/A senha deve ter no mínimo 8 caracteres/i)).toBeInTheDocument();
      expect(confirmPasswordResetMock).not.toHaveBeenCalled();
    });
  });

  it('submits strong password and shows success state', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={['/reset-password?oobCode=valid-code']}>
        <ResetPasswordPage />
      </MemoryRouter>
    );

    const passwordInput = await screen.findByLabelText(/^Nova senha$/i);
    const confirmPasswordInput = await screen.findByLabelText(/^Confirmar nova senha$/i);

    await user.type(passwordInput, 'StrongPass1');
    await user.type(confirmPasswordInput, 'StrongPass1');
    await user.click(screen.getByRole('button', { name: /redefinir senha/i }));

    await waitFor(() => {
      expect(confirmPasswordResetMock).toHaveBeenCalledWith(
        expect.anything(),
        'valid-code',
        'StrongPass1'
      );
      expect(screen.getByText(/senha redefinida com sucesso/i)).toBeInTheDocument();
    });
  });
});
