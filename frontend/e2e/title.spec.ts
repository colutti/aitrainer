import { test, expect } from '@playwright/test';

test.describe('App Title', () => {
  test('should have the correct title', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle('FityQ');
  });
});
