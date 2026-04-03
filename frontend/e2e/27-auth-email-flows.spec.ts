import { test, expect } from '@playwright/test';

import {
  buildE2EUserCredentials,
  loginViaUi,
  registerAndVerifyViaEmulator,
} from './helpers/bootstrap';
import { resetPasswordViaEmulator } from './helpers/firebase-emulator';

test.use({ storageState: { cookies: [], origins: [] } });

test.describe('Auth Email Flows (Firebase Emulator)', () => {
  test('verifies email via emulator and allows first login', async ({ page }, testInfo) => {
    const user = buildE2EUserCredentials(testInfo, 'verify');

    await registerAndVerifyViaEmulator(page, user);
    await loginViaUi(page, user);

    await expect(page).toHaveURL(/\/onboarding(?:\?.*)?$/, { timeout: 20000 });
    await expect(page.getByText(/Your Profile|Seu Perfil|Tu perfil/i)).toBeVisible({ timeout: 20000 });
  });

  test('resets password via emulator and allows login with new password', async ({ page }, testInfo) => {
    const user = buildE2EUserCredentials(testInfo, 'reset');
    const newPassword = 'FityqDemo!2027';

    await registerAndVerifyViaEmulator(page, user);
    await page.goto('/login', { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: /^Login$/i }).click();

    await page.getByTestId('login-email').fill(user.email);
    await page.getByRole('button', { name: /Esqueci a senha/i }).click();
    await expect(
      page.getByText(
        /Enviamos um link para redefinir sua senha no seu e-mail\.|We sent a reset link to your email\.|Te enviamos un enlace para restablecer tu contraseña en tu correo\./i
      )
    ).toBeVisible({ timeout: 20000 });

    await resetPasswordViaEmulator(page.request, user.email, newPassword);

    await page.getByTestId('login-password').fill(newPassword);
    await page.getByRole('button', { name: /^Entrar$/i }).click();

    await expect(page).toHaveURL(/\/onboarding(?:\?.*)?$/, { timeout: 20000 });
  });
});
