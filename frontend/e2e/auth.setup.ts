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
    const email = process.env.E2E_USER_EMAIL || 'rafacolucci@gmail.com';
    const password = process.env.E2E_USER_PASSWORD;
    
    if (!password) {
        console.warn('⚠️  E2E_USER_PASSWORD environment variable not set. E2E authentication may fail.');
    }
    
    await emailInput.fill(email);
    await passwordInput.fill(password || '');

    // Submit form
    await page.click('button[type="submit"]');

    // Wait for navigation to home
    await page.waitForURL('http://localhost:3000/', { timeout: 10000 }).catch(() => void 0);
    await page.waitForTimeout(1000);
  }

  // Save storage state
  await page.context().storageState({ path: authFile });
});
