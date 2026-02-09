import { test, expect } from '@playwright/test';

test.describe('Onboarding Flow', () => {
  test.beforeEach(async ({ page }) => {
    // PROTECT BACKEND
    await page.route(url => url.pathname.startsWith('/api/'), async (route) => {
      await route.fulfill({ status: 500, body: JSON.stringify({ detail: `Unmocked API call: ${route.request().url()}` }) });
    });
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
