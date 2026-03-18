import { test, expect } from './fixtures';
import { cleanupUserData } from './helpers/cleanup';

test.describe('Nutrition Features', () => {

  test.beforeEach(async ({ api }) => {
    await cleanupUserData(api);
  });

  test('should create and list nutrition logs', async ({ authenticatedPage, api }) => {
    await authenticatedPage.goto('/dashboard/body/nutrition');
    await authenticatedPage.waitForLoadState('networkidle');

    // 1. Open drawer
    await authenticatedPage.getByRole('button', { name: /Registrar Dieta/i }).first().click();
    
    // 2. Fill form
    await authenticatedPage.locator('input[name="calories"]').first().fill('2200');
    await authenticatedPage.locator('input[name="protein_grams"]').first().fill('150');
    
    // 3. Save
    await authenticatedPage.waitForTimeout(1000);
    const saveBtn = authenticatedPage.locator('button').filter({ hasText: /Salvar/i }).last();
    await saveBtn.click({ force: true });

    // 4. Verify in list
    // Use a more flexible check for the text since it might be formatted
    await expect(authenticatedPage.locator('.bg-dark-card').filter({ hasText: /2/ }).filter({ hasText: /200/ }).first()).toBeVisible({ timeout: 15000 });
  });

  test('should delete a nutrition log', async ({ authenticatedPage, api }) => {
    // 1. Setup
    await api.post('/nutrition/log', {
      calories: 3000,
      protein_grams: 200,
      carbs_grams: 300,
      fat_grams: 80,
      date: new Date().toISOString(),
      source: 'manual'
    });

    await authenticatedPage.goto('/dashboard/body/nutrition');
    await authenticatedPage.waitForLoadState('networkidle');
    
    // 2. Verify and delete
    const card = authenticatedPage.locator('.bg-dark-card').filter({ hasText: /3/ }).filter({ hasText: /000/ }).first();
    await expect(card).toBeVisible({ timeout: 15000 });
    
    await card.hover();
    const deleteBtn = card.locator('button[title*="Excluir"]').first();
    // In Nutrition Tab, delete is direct (no modal)
    await deleteBtn.click({ force: true });

    // 3. Verify gone
    await expect(authenticatedPage.getByText('3000')).not.toBeVisible({ timeout: 15000 });
  });
});
