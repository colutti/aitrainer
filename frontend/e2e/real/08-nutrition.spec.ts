import { test, expect } from './fixtures';
import { cleanupUserData } from './helpers/cleanup';

test.describe('Nutrition Features', () => {

  test.beforeEach(async ({ api }) => {
    await cleanupUserData(api);
  });

  test('should create and list nutrition logs', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/body/nutrition');
    await authenticatedPage.waitForLoadState('networkidle');
    
    // Check empty state
    await expect(authenticatedPage.getByText(/Nenhum registro encontrado/i)).toBeVisible();

    // Click "Registrar Refeição" button to open drawer
    await authenticatedPage.locator('button:has-text("Registrar Refeição")').or(authenticatedPage.locator('button.fixed.bottom-24')).click();
    
    // Fill form
    await authenticatedPage.fill('input[name="calories"]', '2200');
    await authenticatedPage.fill('input[name="protein_grams"]', '160');
    await authenticatedPage.fill('input[name="carbs_grams"]', '250');
    await authenticatedPage.fill('input[name="fat_grams"]', '60');
    
    // Submit
    await authenticatedPage.locator('button[type="submit"]').click();

    // Success toast
    await expect(authenticatedPage.getByText(/sucesso/i).first()).toBeVisible();

    // Check list entries
    await expect(authenticatedPage.getByText('2200')).toBeVisible();
    await expect(authenticatedPage.getByText('160g')).toBeVisible();
  });

  test('should delete a nutrition log', async ({ authenticatedPage, api }) => {
    // 1. Setup data
    await api.post('/nutrition/log', {
      calories: 3000,
      protein_grams: 200,
      carbs_grams: 400,
      fat_grams: 80,
      date: new Date().toISOString(),
      source: 'manual'
    });

    await authenticatedPage.goto('/dashboard/body/nutrition');
    await authenticatedPage.waitForLoadState('networkidle');
    await expect(authenticatedPage.getByText('3000')).toBeVisible();

    // 2. Delete
    await authenticatedPage.locator('button:has-text("Excluir")').or(authenticatedPage.locator('.lucide-trash-2')).first().click();
    await authenticatedPage.locator('button:has-text("Confirmar")').or(authenticatedPage.locator('button:has-text("Excluir")')).last().click();

    // Verify
    await expect(authenticatedPage.getByText('3000')).not.toBeVisible();
    await expect(authenticatedPage.getByText(/Nenhum registro encontrado/i)).toBeVisible();
  });
});
