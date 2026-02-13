import { test as setup } from '@playwright/test';

const authFile = 'playwright/.auth/user.json';

setup('authenticate', async ({ page }) => {
  // Go to login
  await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle' });

  // Wait a bit for page to load
  await page.waitForTimeout(1000);

  // Fill login form
  const emailInput = page.locator('input[type="email"]');
  const passwordInput = page.locator('input[type="password"]');

  if (await emailInput.isVisible()) {
    await emailInput.fill('rafacolucci@gmail.com');
    await passwordInput.fill('Let7hu118');

    // Submit form
    await page.click('button[type="submit"]');

    // Wait for navigation to home
    await page.waitForURL('http://localhost:3000/', { timeout: 10000 }).catch(() => {});
    await page.waitForTimeout(1000);
  }

  // Save storage state
  await page.context().storageState({ path: authFile });
});
