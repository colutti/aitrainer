import { test as setup } from '@playwright/test';

const authFile = 'playwright/.auth/integration.json';

setup('authenticate-integration', async ({ page }) => {
  console.log('🔐 Authenticating integration user...');
  
  await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle' });

  const emailInput = page.locator('input[type="email"]');
  const passwordInput = page.locator('input[type="password"]');

  if (await emailInput.isVisible()) {
    const email = process.env.E2E_USER_EMAIL ?? 'rafacolucci@gmail.com';
    const password = process.env.E2E_USER_PASSWORD;
    
    if (!password) {
        throw new Error('❌ E2E_USER_PASSWORD environment variable not set.');
    }
    
    await emailInput.fill(email);
    await passwordInput.fill(password);
    await page.click('button[type="submit"]');

    // Wait for navigation and verify we are in
    await page.waitForURL('**/dashboard', { timeout: 15000 });
    console.log('✅ Integration user authenticated successfully.');
  } else {
    console.log('ℹ️  Login form not visible, maybe already authenticated?');
  }

  // Save storage state
  await page.context().storageState({ path: authFile });
});
