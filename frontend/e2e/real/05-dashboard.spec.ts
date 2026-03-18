import { test, expect } from './fixtures';
import { cleanupUserData } from './helpers/cleanup';

test.describe('Dashboard Features', () => {

  test.beforeEach(async ({ api }) => {
    await cleanupUserData(api);
  });

  test('should display all main dashboard widgets and data correctly', async ({ authenticatedPage, api }) => {
    await authenticatedPage.setViewportSize({ width: 1440, height: 900 });
    
    // 1. Setup mock data via API
    await api.post('/weight', {
      weight_kg: 78.5,
      body_fat_pct: 18.2,
      muscle_mass_pct: 40.5,
      date: new Date().toISOString().split('T')[0]
    });

    await api.post('/nutrition/log', {
      calories: 1800,
      protein_grams: 150,
      carbs_grams: 180,
      fat_grams: 50,
      date: new Date().toISOString(),
      source: 'manual'
    });

    await authenticatedPage.goto('/dashboard');
    await authenticatedPage.waitForLoadState('networkidle');

    // 2. Verify Dashboard loaded
    await expect(authenticatedPage.locator('#widget-metabolism')).toBeVisible({ timeout: 15000 });

    // 3. Verify Greeting
    await expect(authenticatedPage.getByText(/Bom dia|Boa tarde|Boa noite/i)).toBeVisible();
    await expect(authenticatedPage.getByRole('heading', { name: /E2E Bot/i })).toBeVisible();

    // 4. Verify Stats Cards
    await expect(authenticatedPage.getByText(/Meta Diária/i).first()).toBeVisible();
    await expect(authenticatedPage.getByText('2436').first()).toBeVisible();

    // 5. Verify Recent Activities
    await expect(authenticatedPage.getByText(/Pesagem/i).first()).toBeVisible();
    await expect(authenticatedPage.getByText(/Refeição/i).first()).toBeVisible();

    // 6. Verify WidgetPRs (should show empty state message)
    await expect(authenticatedPage.getByText(/Nenhum recorde ainda/i).first()).toBeVisible();
  });

  test('should show payment success toast notification', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard?payment=success');
    
    await expect(authenticatedPage.locator('.bg-green-500\\/10').or(authenticatedPage.locator('[data-testid*="toast"]')).first()).toBeVisible({ timeout: 10000 });
    await expect(authenticatedPage.getByText(/sucesso|Bem-vindo/i).first()).toBeVisible();
  });

  test('should show payment cancelled toast notification', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard?payment=cancelled');
    
    await expect(authenticatedPage.locator('.bg-blue-500\\/10').or(authenticatedPage.locator('[data-testid*="toast"]')).first()).toBeVisible({ timeout: 10000 });
    await expect(authenticatedPage.getByText(/interrompido|cancelado/i).first()).toBeVisible();
  });
});
