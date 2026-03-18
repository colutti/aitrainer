import { test, expect } from './fixtures';
import { cleanupUserData } from './helpers/cleanup';

test.describe('Weight Features', () => {

  test.beforeEach(async ({ api }) => {
    await cleanupUserData(api);
  });

  test('should create and list weight logs', async ({ authenticatedPage, api }) => {
    await authenticatedPage.goto('/dashboard/body/weight');
    await authenticatedPage.waitForLoadState('networkidle');
    
    // 1. Open drawer
    await authenticatedPage.getByRole('button', { name: /Registrar Peso/i }).first().click();
    
    // 2. Fill form
    await authenticatedPage.locator('input[name="weight_kg"]').first().fill('82.5');
    // Body fat is mandatory in useWeightTab
    await authenticatedPage.locator('input[name="body_fat_pct"]').first().fill('15');
    
    // 3. Save
    await authenticatedPage.waitForTimeout(1000);
    const saveBtn = authenticatedPage.locator('button').filter({ hasText: /Salvar/i }).last();
    await saveBtn.click({ force: true });

    // 4. Verify in list (it uses .toFixed(2))
    await expect(authenticatedPage.getByText('82.50').first()).toBeVisible({ timeout: 15000 });
  });

  test('should delete a weight log', async ({ authenticatedPage, api }) => {
    // 1. Setup
    await api.post('/weight', {
      weight_kg: 90.0,
      body_fat_pct: 20,
      date: new Date().toISOString().split('T')[0]
    });

    await authenticatedPage.goto('/dashboard/body/weight');
    await authenticatedPage.waitForLoadState('networkidle');
    
    // 2. Verify and delete
    await expect(authenticatedPage.getByText('90.00').first()).toBeVisible({ timeout: 15000 });
    
    const card = authenticatedPage.locator('.bg-dark-card').filter({ hasText: /90/ }).first();
    await card.hover();
    const deleteBtn = card.locator('button[title*="Excluir"]').first();
    // In Weight Tab, delete is direct (no modal)
    await deleteBtn.click({ force: true });

    // 3. Verify gone
    await expect(authenticatedPage.getByText('90.00')).not.toBeVisible({ timeout: 15000 });
  });
});
