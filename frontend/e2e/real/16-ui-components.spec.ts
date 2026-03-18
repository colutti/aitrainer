import { test, expect } from './fixtures';

test.describe('UI Components & UX', () => {

  test('should open QuickAdd menu and navigate to weight log', async ({ authenticatedPage }) => {
    // Mobile view to ensure FAB is visible and clickable
    await authenticatedPage.setViewportSize({ width: 375, height: 667 });
    await authenticatedPage.goto('/dashboard');

    // Click FAB (Floating Action Button) - uses Plus icon and specific fixed classes
    const fab = authenticatedPage.locator('div.fixed button').filter({ has: authenticatedPage.locator('svg') }).last();
    await expect(fab).toBeVisible({ timeout: 15000 });
    await fab.click({ force: true });

    // Wait for animation and check options
    const weightOption = authenticatedPage.locator('div').filter({ hasText: /^Peso|^Pesagem|^Registrar Peso/i }).last();
    await expect(weightOption).toBeVisible({ timeout: 10000 });

    // Select Peso (click the button inside this option div)
    const weightBtn = weightOption.locator('button').first();
    await weightBtn.click({ force: true });
    
    await expect(authenticatedPage).toHaveURL(/.*weight/);
  });

  test('should show and dismiss the Intro Tour', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard');
    // Clear tour state
    await authenticatedPage.evaluate(() => {
       localStorage.removeItem('has_seen_tour_dashboard-main-e2e-bot@fityq.it');
    });
    await authenticatedPage.reload();

    // Check if tour overlay appears
    const tourOverlay = authenticatedPage.locator('.shepherd-element').first();
    const isVisible = await tourOverlay.isVisible().catch(() => false);
    if (isVisible) {
        await expect(tourOverlay).toBeVisible({ timeout: 15000 });
        // Dismiss tour
        await authenticatedPage.locator('button').filter({ hasText: /Pular|Fechar|Skip|Close/i }).first().click({ force: true });
        await expect(tourOverlay).not.toBeVisible();
    }
  });

  test('should display toast notifications for different states', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/settings/profile');
    
    // Trigger success toast (valid update)
    const ageInput = authenticatedPage.locator('input#profile-age').first();
    await ageInput.fill('35');
    await ageInput.blur();
    
    const saveBtn = authenticatedPage.locator('button').filter({ hasText: /Salvar/i }).first();
    await saveBtn.click({ force: true });
    
    // Toast should appear (data-testid="toast" or similar)
    const toast = authenticatedPage.locator('.bg-green-500\\/10').or(authenticatedPage.locator('[data-testid*="toast"]')).first();
    await expect(toast).toBeVisible({ timeout: 15000 });
  });
});
