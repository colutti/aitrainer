import { test, expect } from './fixtures';
import { cleanupUserData } from './helpers/cleanup';

test.describe('Metabolism Features', () => {

  test.beforeEach(async ({ api }) => {
    await cleanupUserData(api);
  });

  test('should show metabolism stats on dashboard', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard');
    await authenticatedPage.waitForLoadState('networkidle');

    // 1. Check if the dashboard is loaded by looking for metabolism-related text or the widget ID
    await expect(authenticatedPage.locator('#widget-metabolism')).toBeVisible({ timeout: 15000 });
    
    // 2. Check for values from VirtualBackend (TDEE is 2436 in mock)
    await expect(authenticatedPage.getByText('2436').first()).toBeVisible({ timeout: 10000 });
  });
});
