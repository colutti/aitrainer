import { test, expect } from '@playwright/test';

test.describe('Nutrition Feature', () => {
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
    await page.route('**/api/nutrition/stats', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({
        today: { calories: 2000, protein_grams: 150, carbs_grams: 200, fat_grams: 60 },
        daily_target: 2500,
        macro_targets: { protein: 180, carbs: 250, fat: 80 },
        stability_score: 85,
        weekly_adherence: [true, true, true, false, true, true, true]
      }) });
    });

    // Mock history
    const mockLog = {
        id: 'log-1',
        date: '2026-02-08',
        calories: 2000,
        protein_grams: 150,
        carbs_grams: 200,
        fat_grams: 60,
        source: 'Manual',
        description: 'Chicken Salad'
    };
    // Match /api/nutrition, /api/nutrition/list, /api/nutrition/log, with or without query
    await page.route(/\/api\/nutrition(\/list|\/log)?(\?|$)/, async (route) => {
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
    
    await page.goto('/body/nutrition');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'Registrar Dieta' })).toBeVisible();
  });

  test('should verify nutrition page elements', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Registrar Dieta' })).toBeVisible();
    await expect(page.getByText('Histórico Recente')).toBeVisible();
    await expect(page.getByText('Calorias (kcal)')).toBeVisible();
  });

  test('should add a complete nutrition log entry', async ({ page }) => {
    await page.route('**/api/nutrition/log', async (route) => {
      if (route.request().method() === 'POST') {
        const payload = JSON.parse(route.request().postData() || '{}');
        await route.fulfill({ status: 201, body: JSON.stringify({ ...payload, id: 'new-id' }) });
      }
    });

    await page.getByLabel('Calorias (kcal)').fill('2500');
    await page.getByLabel('Proteínas (g)').fill('180');
    await page.getByLabel('Carboidratos (g)').fill('250');
    await page.getByLabel('Gorduras (g)').fill('70');

    await page.getByRole('button', { name: 'Salvar Registro' }).click();

    await expect(page.getByText('Registro nutricional salvo!').first()).toBeVisible();
  });

  test('should edit and delete a nutrition entry', async ({ page }) => {
    // Edit
    await page.getByLabel('Calorias (kcal)').fill('2100');
    await page.getByRole('button', { name: 'Salvar Registro' }).click();
    await expect(page.getByText('Registro nutricional salvo!').first()).toBeVisible();

    // Delete
    await page.route('**/api/nutrition/log-1', async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({ status: 204 });
      }
    });

    // Verify log is visible via delete button
    await expect(page.locator('button[title="Excluir registro"]').first()).toBeVisible();

    // In NutritionLogCard, button has title "Excluir registro"
    // Note: There is no confirmation dialog in the current implementation
    await page.locator('button[title="Excluir registro"]').first().click({ force: true });
    
    await expect(page.getByText('Registro removido').first()).toBeVisible();
  });
});
