import { test, expect } from '@playwright/test';

test.describe('Settings Feature', () => {
  test.beforeEach(async ({ page }) => {
    // CAPTURE BROWSER LOGS
    page.on('console', msg => {
        if (msg.type() === 'error') console.log('BROWSER ERROR:', msg.text());
    });

    // Reset storage state for mocked tests
    await page.context().addInitScript(() => {
      window.localStorage.setItem('auth_token', 'mock-jwt');
      window.localStorage.setItem('i18nextLng', 'pt-BR');
      window.localStorage.setItem('has_seen_tour_dashboard-main-user@ex.com', 'true');
    });

    // Mock specific API calls
    await page.route(url => url.pathname === '/api/user/me', async (route) => {
      await route.fulfill({ 
        status: 200, 
        contentType: 'application/json',
        body: JSON.stringify({ 
            name: 'User', 
            email: 'user@ex.com', 
            role: 'user',
            onboarding_completed: true
        }) 
      });
    });

    await page.route(url => url.pathname === '/api/user/profile', async (route) => {
        await route.fulfill({ 
          status: 200, 
          contentType: 'application/json',
          body: JSON.stringify({ 
            email: 'test@ex.com',
            age: 25,
            height: 175,
            gender: 'male',
            goal_type: 'maintain',
            weekly_rate: 0,
            display_name: 'Test User'
          }) 
        });
    });

    // CATCH-ALL only for /api/ paths to avoid blocking static assets
    await page.route(url => url.pathname.startsWith('/api/') 
        && url.pathname !== '/api/user/me' 
        && url.pathname !== '/api/user/profile'
        && !url.pathname.includes('/user/update_profile')
        && !url.pathname.includes('/user/update_identity')
        && !url.pathname.includes('/trainer/available_trainers')
        && !url.pathname.includes('/trainer/trainer_profile')
        && !url.pathname.includes('/trainer/update_trainer_profile')
        && !url.pathname.includes('/integrations/'), async (route) => {
        await route.fulfill({ status: 200, body: JSON.stringify({}) });
    });

    await page.goto('/dashboard/settings/profile');
    await page.waitForLoadState('networkidle');
  });

  test('should load all profile fields with mock values', async ({ page }) => {
    await expect(page.getByLabel(/Idade/i)).toHaveValue('25');
    await expect(page.getByLabel(/Altura/i)).toHaveValue('175');
  });

  test('should update profile information', async ({ page }) => {
    await page.route(/\/api\/user\/update_profile/, async (route) => {
        await route.fulfill({ status: 200, body: JSON.stringify({ success: true }) });
    });

    await page.route(/\/api\/user\/update_identity/, async (route) => {
        await route.fulfill({ status: 200, body: JSON.stringify({ success: true }) });
    });

    await page.getByLabel(/Idade/i).fill('30');
    await page.getByLabel(/Gênero/i).fill('Masculino');
    
    await page.getByRole('button', { name: /Salvar Alterações/i }).click();
    await expect(page.getByText(/Perfil atualizado com sucesso/i).first()).toBeVisible();
  });

  test('should switch trainer', async ({ page }) => {
    await page.route('**/api/trainer/available_trainers', async (route) => {
        await route.fulfill({ status: 200, body: JSON.stringify([
            { trainer_id: 'atlas', name: 'Atlas', short_description: 'Powerlifting' },
            { trainer_id: 'luna', name: 'Luna', short_description: 'Yoga' }
        ]) });
    });

    await page.route('**/api/trainer/trainer_profile', async (route) => {
        await route.fulfill({ status: 200, body: JSON.stringify({ trainer_type: 'atlas' }) });
    });

    await page.getByRole('link', { name: /Treinador AI/i, exact: true }).click();
    await page.waitForURL('**/settings/trainer');

    await expect(page.getByText('Luna')).toBeVisible();
    await page.getByText('Luna').click();
    
    await page.route('**/api/trainer/update_trainer_profile', async (route) => {
        await route.fulfill({ status: 200, body: JSON.stringify({ success: true }) });
    });

    await page.getByRole('button', { name: /Atualizar Treinador/i }).click();
    await expect(page.getByText(/Treinador atualizado com sucesso/i).first()).toBeVisible();
  });

  test('should view integrations', async ({ page }) => {
    await page.route('**/api/integrations/hevy/status', async (route) => {
        await route.fulfill({ status: 200, body: JSON.stringify({ enabled: true, hasKey: true, apiKeyMasked: '****1234' }) });
    });
    await page.route('**/api/integrations/telegram/status', async (route) => {
        await route.fulfill({ status: 200, body: JSON.stringify({ connected: true, username: 'test_user' }) });
    });

    await page.getByRole('link', { name: /Integrações/i }).click();
    await page.waitForURL('**/settings/integrations');

    await expect(page.getByText('Hevy')).toBeVisible();
    await expect(page.getByText('Telegram Bot')).toBeVisible();
  });
});
