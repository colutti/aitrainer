import { test, expect } from '@playwright/test';

test.describe('Onboarding Flow', () => {
  test.beforeEach(async ({ page }) => {
    // PROTECT BACKEND
    await page.route(url => url.pathname.startsWith('/api/'), async (route) => {
      await route.fulfill({ status: 500, body: JSON.stringify({ detail: `Unmocked API call: ${route.request().url()}` }) });
    });
  });

  test('should show error for missing token', async ({ page }) => {
    // Navigate without any token param
    await page.goto('/onboarding');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText('Token de convite não encontrado.')).toBeVisible();
  });

  test('should show error for expired token', async ({ page }) => {
    await page.route('**/api/onboarding/validate*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ valid: false, reason: 'expired' }) });
    });

    await page.goto('/onboarding?token=expired-token');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText('O convite expirou.')).toBeVisible();
  });

  test('should show error for already used token', async ({ page }) => {
    await page.route('**/api/onboarding/validate*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ valid: false, reason: 'already_used' }) });
    });

    await page.goto('/onboarding?token=used-token');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText('Convite já utilizado.')).toBeVisible();
  });

  test('should disable next when password too short', async ({ page }) => {
    await page.route('**/api/onboarding/validate*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ valid: true }) });
    });

    await page.goto('/onboarding?token=valid-token');
    await page.waitForLoadState('networkidle');

    // Password < 8 chars
    await page.getByPlaceholder('Senha', { exact: true }).fill('Ab1');
    await page.getByPlaceholder('Confirmar Senha').fill('Ab1');

    await expect(page.getByRole('button', { name: 'Próximo' })).toBeDisabled();
  });

  test('should disable next when password has no numbers', async ({ page }) => {
    await page.route('**/api/onboarding/validate*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ valid: true }) });
    });

    await page.goto('/onboarding?token=valid-token');
    await page.waitForLoadState('networkidle');

    // Password without numbers
    await page.getByPlaceholder('Senha', { exact: true }).fill('abcdefgh');
    await page.getByPlaceholder('Confirmar Senha').fill('abcdefgh');

    await expect(page.getByRole('button', { name: 'Próximo' })).toBeDisabled();
  });

  test('should disable next when passwords dont match', async ({ page }) => {
    await page.route('**/api/onboarding/validate*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ valid: true }) });
    });

    await page.goto('/onboarding?token=valid-token');
    await page.waitForLoadState('networkidle');

    await page.getByPlaceholder('Senha', { exact: true }).fill('Password123');
    await page.getByPlaceholder('Confirmar Senha').fill('Password456');

    await expect(page.getByRole('button', { name: 'Próximo' })).toBeDisabled();
  });

  test('should disable next when age below minimum in step 2', async ({ page }) => {
    await page.route('**/api/onboarding/validate*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ valid: true }) });
    });

    await page.goto('/onboarding?token=valid-token');
    await page.waitForLoadState('networkidle');

    // Complete step 1
    await page.getByPlaceholder('Senha', { exact: true }).fill('Password123');
    await page.getByPlaceholder('Confirmar Senha').fill('Password123');
    await page.getByRole('button', { name: 'Próximo' }).click();

    // Step 2: set age below 18
    await expect(page.getByText('Seu Perfil')).toBeVisible();
    await page.locator('#age').fill('15');
    await page.locator('#weight').fill('60');
    await page.locator('#height').fill('170');

    await expect(page.getByRole('button', { name: 'Próximo' }).last()).toBeDisabled();
  });

  test('should navigate back from step 2 to step 1', async ({ page }) => {
    await page.route('**/api/onboarding/validate*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ valid: true }) });
    });

    await page.goto('/onboarding?token=valid-token');
    await page.waitForLoadState('networkidle');

    // Go to step 2
    await page.getByPlaceholder('Senha', { exact: true }).fill('Password123');
    await page.getByPlaceholder('Confirmar Senha').fill('Password123');
    await page.getByRole('button', { name: 'Próximo' }).click();

    await expect(page.getByText('Seu Perfil')).toBeVisible();

    // Go back to step 1
    await page.getByRole('button', { name: 'Voltar' }).click();

    await expect(page.getByText('Criar Senha')).toBeVisible();
  });

  test('should complete full onboarding flow', async ({ page }) => {
     const mockToken = 'valid-token';
     
     // 1. Validate Token
     await page.route(`**/api/onboarding/validate?token=${mockToken}`, async (route) => {
         await route.fulfill({ status: 200, body: JSON.stringify({ valid: true }) });
     });

     await page.route('**/api/onboarding/complete', async (route) => {
         await route.fulfill({ status: 201, body: JSON.stringify({ token: 'new-token' }) });
     });

     await page.route('**/api/user/me', async (route) => {
        await route.fulfill({ status: 200, body: JSON.stringify({ name: 'User', email: 'user@ex.com', role: 'user' }) });
     });

     await page.goto(`/onboarding?token=${mockToken}`);

     // 2. Step 1: Password
     await expect(page.getByText('Criar Senha')).toBeVisible();
     await page.getByPlaceholder('Senha', { exact: true }).fill('Password123');
     await page.getByPlaceholder('Confirmar Senha').fill('Password123');
     await page.getByRole('button', { name: 'Próximo' }).click();

     // 3. Step 2: Profile
     await expect(page.getByText('Seu Perfil')).toBeVisible();
     await page.locator('#age').fill('25');
     await page.locator('#weight').fill('75');
     await page.locator('#height').fill('180');
     await page.getByRole('button', { name: 'Próximo' }).click();

     // 4. Step 3: Trainer
     await expect(page.getByText('Escolha seu Treinador')).toBeVisible();
     await page.getByText('Luna').click();
     
     await page.route('**/api/onboarding/complete', async (route) => {
         await route.fulfill({ status: 200, body: JSON.stringify({ token: 'new-jwt-token' }) });
     });

     await page.getByRole('button', { name: 'Finalizar Cadastro' }).click();

     // 5. Success redirect
     await expect(page).toHaveURL('/');
  });
});
