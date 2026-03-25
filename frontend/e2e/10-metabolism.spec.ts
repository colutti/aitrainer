import { test, expect } from './fixtures';

test.describe('Metabolism Features', () => {

  test('should show metabolism stats on dashboard', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard');
    await authenticatedPage.waitForLoadState('networkidle');

    // 1. Check if the dashboard is loaded by looking for the widget testid
    await expect(authenticatedPage.getByTestId('widget-metabolism')).toBeVisible({ timeout: 15000 });
    
    // 2. Check for TDEE value (using more specific selector to avoid strict mode violation)
    const tdeeValue = authenticatedPage.getByTestId('widget-metabolism').locator('p.text-emerald-400').first();
    await expect(tdeeValue).toBeVisible({ timeout: 10000 });
    await expect(tdeeValue).toHaveText(/\d{4}/);
  });
});
