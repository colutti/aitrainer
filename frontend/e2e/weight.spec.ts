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

  test('should fill ALL optional body composition fields', async ({ page }) => {
    // Fill mandatory fields
    await page.getByLabel('Peso (kg)').fill('80');
    await page.getByLabel('Gordura Corporal (%)').fill('18');
    await page.getByLabel('Massa Muscular (%)').fill('38');

    // Fill optional body composition fields (no explicit id - use label+sibling selector)
    await page.locator('label:has-text("Água Corporal (%)") + div input').fill('55.5');
    await page.locator('label:has-text("Massa Óssea (kg)") + div input').fill('3.5');
    await page.locator('label:has-text("Gordura Visceral") + div input').fill('8');
    await page.locator('label:has-text("TMB (kcal)") + div input').fill('1850');

    await page.getByRole('button', { name: 'Salvar Registro' }).click();

    await expect(page.getByText('Registro de peso salvo!').first()).toBeVisible();
  });

  test('should fill ALL body measurement fields', async ({ page }) => {
    // Fill mandatory fields
    await page.getByLabel('Peso (kg)').fill('80');
    await page.getByLabel('Gordura Corporal (%)').fill('18');
    await page.getByLabel('Massa Muscular (%)').fill('38');

    // Fill all 10 measurement fields (fields without explicit id use label+sibling selector)
    await page.locator('label:has-text("Pescoço") + div input').fill('38');
    await page.locator('label:has-text("Peito") + div input').fill('100');
    await page.getByLabel('Cintura').fill('85'); // has id="waist_cm"
    await page.locator('label:has-text("Quadril") + div input').fill('95');
    await page.locator('label:has-text("Bíceps (D)") + div input').fill('35');
    await page.locator('label:has-text("Bíceps (E)") + div input').fill('34');
    await page.locator('label:has-text("Coxa (D)") + div input').fill('55');
    await page.locator('label:has-text("Coxa (E)") + div input').fill('54');
    await page.locator('label:has-text("Pant. (D)") + div input').fill('38');
    await page.locator('label:has-text("Pant. (E)") + div input').fill('37');

    await page.getByRole('button', { name: 'Salvar Registro' }).click();

    await expect(page.getByText('Registro de peso salvo!').first()).toBeVisible();
  });

  test('should validate mandatory body_fat_pct and muscle_mass_pct fields', async ({ page }) => {
    // Fill only weight_kg, leave fat and muscle empty
    await page.getByLabel('Peso (kg)').fill('80');
    await page.getByRole('button', { name: 'Salvar Registro' }).click();

    await expect(page.getByText('Gordura corporal é obrigatório')).toBeVisible();
    await expect(page.getByText('Massa muscular é obrigatório')).toBeVisible();
  });

  test('should validate optional field boundaries', async ({ page }) => {
    // Fill mandatory fields correctly
    await page.getByLabel('Peso (kg)').fill('80');
    await page.getByLabel('Gordura Corporal (%)').fill('18');
    await page.getByLabel('Massa Muscular (%)').fill('38');

    // Fill optional fields with out-of-range values (no explicit id, use label+sibling selector)
    await page.locator('label:has-text("Água Corporal (%)") + div input').fill('1'); // min is 2
    await page.locator('label:has-text("Massa Óssea (kg)") + div input').fill('25'); // max is 20
    await page.locator('label:has-text("Gordura Visceral") + div input').fill('55'); // max is 50
    await page.locator('label:has-text("TMB (kcal)") + div input').fill('400'); // min is 500

    await page.getByRole('button', { name: 'Salvar Registro' }).click();

    await expect(page.getByText('Água corporal deve ser ao menos 2')).toBeVisible();
    await expect(page.getByText('Massa óssea deve ser no máximo 20')).toBeVisible();
    await expect(page.getByText('Gordura visceral deve ser no máximo 50')).toBeVisible();
    await expect(page.getByText('TMB deve ser ao menos 500')).toBeVisible();
  });

  test('should validate measurement field boundaries', async ({ page }) => {
    // Fill mandatory fields correctly
    await page.getByLabel('Peso (kg)').fill('80');
    await page.getByLabel('Gordura Corporal (%)').fill('18');
    await page.getByLabel('Massa Muscular (%)').fill('38');

    // Fill measurements with out-of-range values (no explicit id, use label+sibling selector)
    await page.locator('label:has-text("Pescoço") + div input').fill('15'); // min is 20
    await page.locator('label:has-text("Peito") + div input').fill('250'); // max is 200

    await page.getByRole('button', { name: 'Salvar Registro' }).click();

    await expect(page.getByText('Pescoço deve ser ao menos 20')).toBeVisible();
    await expect(page.getByText('Peito deve ser no máximo 200')).toBeVisible();
  });

  test('should validate notes max length', async ({ page }) => {
    // Fill mandatory fields correctly
    await page.getByLabel('Peso (kg)').fill('80');
    await page.getByLabel('Gordura Corporal (%)').fill('18');
    await page.getByLabel('Massa Muscular (%)').fill('38');

    // Fill notes with 501 characters (one over the limit)
    await page.getByLabel('Observações').fill('A'.repeat(501));

    await page.getByRole('button', { name: 'Salvar Registro' }).click();

    await expect(page.getByText('Máximo de 500 caracteres')).toBeVisible();
  });

  test('should handle API error on save', async ({ page }) => {
    // Override POST to return error
    await page.route(/\/api\/weight(\?|$)/, async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({ status: 500, body: JSON.stringify({ detail: 'Internal Server Error' }) });
      } else {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({ logs: [mockLog], total: 1, page: 1, page_size: 10, total_pages: 1 })
        });
      }
    });

    await page.getByLabel('Peso (kg)').fill('80');
    await page.getByLabel('Gordura Corporal (%)').fill('18');
    await page.getByLabel('Massa Muscular (%)').fill('38');

    await page.getByRole('button', { name: 'Salvar Registro' }).click();

    await expect(page.getByText('Erro ao salvar registro de peso.').first()).toBeVisible();
  });

  test('should handle API error on delete', async ({ page }) => {
    // Override DELETE to return error
    await page.route(/\/api\/weight\/.+/, async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({ status: 500, body: JSON.stringify({ detail: 'Internal Server Error' }) });
      }
    });

    await page.getByTitle('Excluir registro').click();

    await expect(page.getByText('Erro ao remover registro.').first()).toBeVisible();
  });
});
