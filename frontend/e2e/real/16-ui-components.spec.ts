import { test, expect } from './fixtures';

test.describe('UI Components & UX', () => {

  test('should open QuickAdd menu and navigate to weight log', async ({ authenticatedPage }) => {
    await authenticatedPage.setViewportSize({ width: 375, height: 667 }); // Mobile for FAB visibility usually
    await authenticatedPage.goto('/dashboard');

    // Click FAB (Floating Action Button)
    const fab = authenticatedPage.locator('button.fixed.bottom-20');
    await fab.click();

    // Verify options
    await expect(authenticatedPage.getByText('Peso')).toBeVisible();
    await expect(authenticatedPage.getByText('Dieta')).toBeVisible();

    // Select Peso
    await authenticatedPage.getByText('Peso').click();
    await expect(authenticatedPage).toHaveURL(/.*weight/);
    
    // Drawer should be open
    await expect(authenticatedPage.getByText('Adicionar Peso')).toBeVisible();
  });

  test('should show and dismiss the Intro Tour', async ({ authenticatedPage }) => {
    // Reset tour state in localStorage via init script is already handled in fixtures.ts if we pass correct keys
    // For this test, let's manually clear it to see it start
    await authenticatedPage.goto('/dashboard');
    await authenticatedPage.evaluate(() => {
       localStorage.removeItem('has_seen_tour_dashboard-main-e2e-bot@fityq.it');
    });
    await authenticatedPage.reload();

    // Check if tour overlay appears
    // Shepherd.js usually adds specific classes
    const tourOverlay = authenticatedPage.locator('.shepherd-element');
    await expect(tourOverlay).toBeVisible({ timeout: 10000 });

    // Dismiss tour
    await authenticatedPage.locator('button:has-text("Pular")').or(authenticatedPage.locator('button:has-text("Fechar")')).click();
    await expect(tourOverlay).not.toBeVisible();
  });

  test('should display toast notifications for different states', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard');
    
    // We can trigger a toast by doing something (like a failed action or just mock it if we have a test route)
    // But since we want "real" tests, let's trigger it via a failed settings update
    await authenticatedPage.goto('/settings/profile');
    await authenticatedPage.fill('input[name="age"]', '5'); // Invalid age
    await authenticatedPage.locator('button:has-text("Salvar Alterações")').last().click();

    // Error toast
    await expect(authenticatedPage.locator('.bg-red-500\\/10')).toBeVisible();
    
    // Success toast (valid update)
    await authenticatedPage.fill('input[name="age"]', '30');
    await authenticatedPage.locator('button:has-text("Salvar Alterações")').last().click();
    await expect(authenticatedPage.locator('.bg-green-500\\/10')).toBeVisible();
  });
});
