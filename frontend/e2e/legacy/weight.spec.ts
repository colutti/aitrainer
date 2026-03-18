import { test, expect } from '@playwright/test';

test.describe('Weight Tracking Feature', () => {
  const mockLog = {
    id: 'log-1',
    date: '2023-01-01',
    weight_kg: 80,
    body_fat_pct: 18,
    muscle_mass_pct: 38
  };

  test.beforeEach(async ({ page }) => {
    // Reset storage state
    await page.context().addInitScript(() => {
      window.localStorage.setItem('auth_token', 'mock-jwt');
      window.localStorage.setItem('i18nextLng', 'pt-BR');
      window.localStorage.setItem('has_seen_tour_dashboard-main-user@ex.com', 'true');
    });

    // Mock user profile
    await page.route(/\/api\/user\/me/, async (route) => {
      await route.fulfill({ 
        status: 200, 
        body: JSON.stringify({ name: 'User', email: 'user@ex.com', role: 'user', onboarding_completed: true }) 
      });
    });

    // Mock stats
    await page.route(/\/api\/weight\/stats/, async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({
        latest: { weight_kg: 80 },
        weight_trend: [],
        fat_trend: [],
        muscle_trend: []
      }) });
    });

    // Mock history
    await page.route(/\/api\/weight(\?|$)/, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            logs: [mockLog],
            total: 1,
            page: 1,
            page_size: 10,
            total_pages: 1
          })
        });
      } else if (route.request().method() === 'POST') {
        const payload = JSON.parse(route.request().postData() || '{}');
        await route.fulfill({ status: 201, body: JSON.stringify({ ...payload, id: 'new-id' }) });
      }
    });

    // FALLBACK for /api/
    await page.route(url => url.pathname.startsWith('/api/') && !url.pathname.includes('/weight'), async (route) => {
        await route.fulfill({ status: 200, body: JSON.stringify({}) });
    });

    await page.goto('/dashboard/body/weight');
    await page.waitForLoadState('networkidle');
  });

  test('should verify weight and stats elements', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Registrar Peso/i })).toBeVisible();
    await expect(page.getByText(/Histórico Recente/i)).toBeVisible();
  });

  test('should add a weight log entry', async ({ page }) => {
    await page.getByRole('button', { name: /Registrar Peso/i }).click();
    await expect(page.getByRole('heading', { name: /Registrar Peso/i })).toBeVisible();

    await page.getByLabel(/Peso \(kg\)/i).fill('85.5');
    await page.getByRole('button', { name: /Salvar Registro/i }).click();

    await expect(page.getByText(/Registro de peso salvo/i).first()).toBeVisible();
  });
});
