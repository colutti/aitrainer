import { test as setup, expect } from '@playwright/test';

const authFile = 'playwright/.auth/user.json';
const apiBaseURL = process.env.E2E_API_BASE_URL ?? 'http://localhost:8000';

setup('authenticate', async ({ page }) => {
  setup.setTimeout(60000); // Increase timeout to 60s for setup

  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));

  const email = process.env.VITE_E2E_USER_EMAIL || 'bot-real@fityq.it';

  console.log(`QA: Bootstrapping E2E authentication for ${email}`);

  const authResponse = await page.request.post(`${apiBaseURL}/user/e2e-login`, {
    data: { email },
  });

  if (!authResponse.ok()) {
    throw new Error(`Failed to bootstrap E2E auth: ${authResponse.status().toString()}`);
  }

  const { token } = await authResponse.json() as { token: string };

  await page.goto('/');
  await page.evaluate((platformToken: string) => {
    localStorage.setItem('auth_token', platformToken);
  }, token);

  await page.goto('/dashboard', { waitUntil: 'networkidle' });

  try {
    await expect(page).toHaveURL(/.*dashboard|.*onboarding/, { timeout: 20000 });
  } catch (error) {
    console.error('QA: Failed to reach authenticated app state.');
    console.log(await page.content());
    throw error;
  }

  // 4. Verify successful load using Premium Dashboard selector
  try {
    await expect(page.getByTestId('dashboard-bento')).toBeVisible({ timeout: 20000 });
  } catch (error) {
    console.error('QA: DASHBOARD BENTO NOT FOUND. HTML Dump:');
    console.log(await page.innerHTML('body'));
    throw error;
  }

  // 5. Save storage state for all tests to reuse
  await page.context().storageState({ path: authFile });
});
