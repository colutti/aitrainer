import { test, expect } from '@playwright/test';

test.describe('Settings Feature', () => {
  test.beforeEach(async ({ context, page }) => {
    // PROTECT BACKEND: Catch-all for any unmocked API calls
    await page.route(url => url.pathname.startsWith('/api/'), async (route) => {
      console.log(`Intercepted unmocked API call: ${route.request().url()}`);
      await route.fulfill({ status: 500, body: JSON.stringify({ detail: `Unmocked API call: ${route.request().url()}` }) });
    });

    // Mock user profile
    await page.route('**/api/user/me', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ name: 'User', email: 'user@ex.com' }) });
    });

    // Set auth token before navigation
    await context.addInitScript(() => {
      window.localStorage.setItem('auth_token', 'mock-jwt');
    });
    
    // Mock user profile (required for some pages)
    await page.route('**/api/user/profile', async (route) => {
        await route.fulfill({ status: 200, body: JSON.stringify({ 
          email: 'test@ex.com',
          age: 25,
          weight: 70,
          height: 175,
          gender: 'male',
          goal_type: 'maintain',
          weekly_rate: 0
        }) });
    });

    await page.goto('/settings/profile');
  });

  test('should update profile information', async ({ page }) => {
    // Mock user profile
    await page.route('**/api/user/profile', async (route) => {
        if (route.request().method() === 'GET') {
            await route.fulfill({ status: 200, body: JSON.stringify({ 
              email: 'test@ex.com',
              age: 25,
              weight: 70,
              height: 175,
              gender: 'male',
              goal_type: 'maintain',
              weekly_rate: 0
            }) });
        }
    });
    
    // Fix: App calls /api/user/update_profile for updates
    await page.route('**/api/user/update_profile', async (route) => {
        await route.fulfill({ status: 200, body: JSON.stringify({ success: true }) });
    });

    await page.reload();
    await page.getByLabel('Idade').fill('30');
    await page.getByRole('button', { name: 'Salvar Alterações' }).click();

    await expect(page.getByText('Perfil atualizado com sucesso').first()).toBeVisible();
  });

  test('should switch trainer', async ({ page }) => {
    // Mock available trainers - Fix endpoint
    await page.route('**/api/trainer/available_trainers', async (route) => {
        await route.fulfill({ status: 200, body: JSON.stringify([
            { trainer_id: 'atlas', name: 'Atlas', short_description: 'Powerlifting' },
            { trainer_id: 'luna', name: 'Luna', short_description: 'Yoga' }
        ]) });
    });

    // Mock current trainer
    await page.route('**/api/trainer/trainer_profile', async (route) => {
        await route.fulfill({ status: 200, body: JSON.stringify({ trainer_type: 'atlas' }) });
    });

    await page.getByRole('link', { name: 'Treinador AI', exact: true }).click();
    await page.waitForURL('/settings/trainer');

    await page.reload();
    
    // Click Luna trainer
    await page.getByText('Luna').click();
    
    await page.route('**/api/trainer/update_trainer_profile', async (route) => {
        if (route.request().method() === 'PUT') {
            await route.fulfill({ status: 200, body: JSON.stringify({ success: true }) });
        }
    });

    await page.getByRole('button', { name: 'Atualizar Treinador' }).click();
    await expect(page.getByText('Treinador atualizado com sucesso!').first()).toBeVisible();
  });

  test('should view integrations', async ({ page }) => {
    // Mock integration status
    await page.route('**/api/integrations/hevy/status', async (route) => {
        await route.fulfill({ status: 200, body: JSON.stringify({ enabled: true, hasKey: true, apiKeyMasked: '****1234' }) });
    });
    await page.route('**/api/integrations/telegram/status', async (route) => {
        await route.fulfill({ status: 200, body: JSON.stringify({ connected: true, username: 'test_user' }) });
    });

    await page.getByRole('link', { name: 'Integrações' }).click();
    await page.waitForURL('/settings/integrations');
    
    await expect(page.getByText('Hevy')).toBeVisible();
    await expect(page.getByText('Telegram Bot')).toBeVisible();
    await expect(page.getByText('test_user')).toBeVisible();
  });
});
