import { test, expect } from './fixtures';
import { cleanupUserData } from './helpers/cleanup';

test.describe('Weight Features', () => {

  test.beforeEach(async ({ api }) => {
    await cleanupUserData(api);
  });

  test('should create and list weight logs', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/body/weight');
    await authenticatedPage.waitForLoadState('networkidle');
    
    // Check empty state
    await expect(authenticatedPage.getByText(/Nenhuma pesagem registrada/i)).toBeVisible();

    // Click "Registrar Peso" button
    await authenticatedPage.locator('button:has-text("Registrar Peso")').or(authenticatedPage.locator('button.fixed.bottom-24')).click();
    
    // Fill form
    await authenticatedPage.fill('input[name="weight"]', '79.2');
    await authenticatedPage.fill('input[name="body_fat_pct"]', '17.5');
    
    // Submit
    await authenticatedPage.locator('button[type="submit"]').click();

    // Success toast
    await expect(authenticatedPage.getByText(/sucesso/i).first()).toBeVisible();

    // Check list entries
    await expect(authenticatedPage.getByText('79.2')).toBeVisible();
    await expect(authenticatedPage.getByText('17.5 %')).toBeVisible();
  });

  test('should delete a weight log', async ({ authenticatedPage, api }) => {
    // 1. Setup data
    await api.post('/weight', {
      weight_kg: 105.0,
      date: new Date().toISOString().split('T')[0] // Use YYYY-MM-DD
    });

    await authenticatedPage.goto('/dashboard/body/weight');
    await authenticatedPage.waitForLoadState('networkidle');
    await expect(authenticatedPage.getByText('105.0')).toBeVisible();

    // 2. Delete
    await authenticatedPage.locator('button:has-text("Excluir")').or(authenticatedPage.locator('.lucide-trash-2')).first().click();
    await authenticatedPage.locator('button:has-text("Confirmar")').click();

    // Verify
    await expect(authenticatedPage.getByText('105.0')).not.toBeVisible();
    await expect(authenticatedPage.getByText(/Nenhuma pesagem registrada/i)).toBeVisible();
  });
});
