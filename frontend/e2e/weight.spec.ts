import { test, expect } from '@playwright/test';

test.describe('Weight Tracking Feature', () => {
  const mockLog = {
    id: 'log-1',
    date: '2023-01-01', // Changed date for consistency with delete mock
    weight_kg: 80,
    body_fat_pct: 18,
    muscle_mass_pct: 38
  };

  test.beforeEach(async ({ context, page }) => {
    // PROTECT BACKEND
    await page.route(url => url.pathname.startsWith('/api/'), async (route) => {
      await route.fulfill({ status: 500, body: JSON.stringify({ detail: `Unmocked API call: ${route.request().url()}` }) });
    });

    // Mock user profile
    await page.route('**/api/user/me', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ name: 'User', email: 'user@ex.com', role: 'user' }) });
    });

    // Mock stats
    await page.route('**/api/weight/stats', async (route) => {
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

    // Set auth token before navigation
    await context.addInitScript(() => {
      window.localStorage.setItem('auth_token', 'mock-jwt');
    });

    await page.goto('/body/weight');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'Registrar Peso' })).toBeVisible();
  });

  test('should verify weight and stats elements', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Registrar Peso' })).toBeVisible();
    await expect(page.getByText('Histórico Recente')).toBeVisible();
  });

  test('should add a complete weight log entry', async ({ page }) => {
    await page.getByLabel('Peso (kg)').fill('85.5');
    await page.getByLabel('Gordura Corporal (%)').fill('20');
    await page.getByLabel('Massa Muscular (%)').fill('35');
    await page.getByLabel('Observações').fill('E2E Test Note');

    // Fill a measurement
    await page.getByLabel('Cintura').fill('90');

    await page.getByRole('button', { name: 'Salvar Registro' }).click();

    // Success toast
    await expect(page.getByText('Registro de peso salvo!').first()).toBeVisible();
  });

  test('should edit an existing weight entry', async ({ page }) => {
    // Click edit button (assume it has title "Editar registro")
    await page.getByTitle('Editar registro').click();

    // Verify fields are populated
    await expect(page.getByLabel('Peso (kg)')).toHaveValue('80');
    await expect(page.getByLabel('Gordura Corporal (%)')).toHaveValue('18');
    await expect(page.getByLabel('Massa Muscular (%)')).toHaveValue('38');

    // Edit and save
    await page.getByLabel('Peso (kg)').fill('81');

    // Mock PUT request to any ID (e.g. log-1)
    await page.route(/\/api\/weight(\/.*)?/, async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ ...mockLog, id: 'log-1', weight_kg: 81 }) });
    });

    await page.getByRole('button', { name: 'Salvar Registro' }).click();
    
    // Check for success message
    await expect(page.getByText('Registro de peso').first()).toBeVisible();
  });

  test('should delete a weight entry', async ({ page }) => {
    // Mock delete for specific ID or date
    await page.route(/\/api\/weight\/.+/, async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({ status: 204 });
      }
    });

    await page.getByTitle('Excluir registro').click();
    await expect(page.getByText('Registro removido').first()).toBeVisible();
  });

  test('should validate weight boundaries', async ({ page }) => {
    await page.getByLabel('Peso (kg)').fill('10'); // Below 30
    await page.getByRole('button', { name: 'Salvar Registro' }).click();
    await expect(page.getByText('Peso deve ser ao menos 30')).toBeVisible();

    await page.getByLabel('Peso (kg)').fill('400'); // Above 300
    await page.getByRole('button', { name: 'Salvar Registro' }).click();
    await expect(page.getByText('Peso deve ser no máximo 300')).toBeVisible();
  });
});
