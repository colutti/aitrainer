import { test, expect } from '@playwright/test';

test('Basic connectivity: Check title and root', async ({ page }) => {
  await page.goto('/login', { waitUntil: 'load' });
  await expect(page).toHaveTitle(/FityQ/i);
  await expect(page.locator('#root')).toBeVisible();
});
