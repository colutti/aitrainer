import { test as setup, expect } from '@playwright/test';

const authFile = 'playwright/.auth/user.json';

setup('authenticate', async ({ page }) => {
  setup.setTimeout(60000); // Increase timeout to 60s for setup

  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));

  const email = process.env.VITE_E2E_USER_EMAIL || 'bot-real@fityq.it';
  const password = process.env.VITE_E2E_USER_PASSWORD || 'password123';

  console.log(`QA: Starting authentication for ${email}`);

  // 1. Go to login
  const response = await page.goto('/login', { waitUntil: 'networkidle' });
  console.log(`QA: Login Page Status: ${response?.status()}`);
  
  if (response?.status() !== 200) {
    console.warn(`QA Warning: Login page returned status ${response?.status()}`);
    console.log('QA Content:', await page.content());
  }

  // Wait for any remaining hydration
  await page.waitForTimeout(1000);

  const inputs = await page.locator('input').count();
  console.log(`QA: Number of inputs found on page: ${inputs}`);

  const emailInput = page.locator('input[name="email"]').first();
  await emailInput.waitFor({ state: 'visible', timeout: 15000 }).catch(() => {
    console.error('QA: EMAIL INPUT NEVER BECAME VISIBLE');
  });

  // Use pressSequentially which is the most reliable method for React Hook Form bypassing hydration/state races
  await emailInput.click();
  await emailInput.pressSequentially(email, { delay: 50 });
  await page.waitForTimeout(500);

  const passInput = page.locator('input[name="password"]').first();
  await passInput.click();
  await passInput.pressSequentially(password, { delay: 50 });
  await page.waitForTimeout(500);
  
  const submitBtn = page.locator('button[type="submit"]').filter({ hasText: /Entrar|Login/i });
  await submitBtn.click();

  console.log('QA: Login submitted, current URL:', page.url());

  // Wait for potential redirect or error
  await page.waitForTimeout(2000);
  console.log('QA: Final URL after 2s:', page.url());

  // 3. Wait for Dashboard with retry for time-sync issues (Token used too early)
  try {
    await expect(page).toHaveURL(/.*dashboard|.*onboarding/, { timeout: 15000 });
    
    // If we landed on onboarding, it means the user state was left incomplete by a previous failed test
    if (page.url().includes('/onboarding')) {
      console.log('QA: Landed on Onboarding during setup, completing it minimally...');
      
      // Step 2: Profile 
      // Ensure gender is selected
      const maleBtn = page.getByRole('button', { name: /Masculino|Male/i }).first();
      await maleBtn.click();
      
      // Fill all required fields
      await page.getByTestId('onboarding-name').locator('input').fill('Real QA Bot');
      await page.getByTestId('onboarding-age').locator('input').fill('30');
      await page.getByTestId('onboarding-height').locator('input').fill('180');
      await page.getByTestId('onboarding-weight').locator('input').fill('80');
      
      const nextBtn = page.getByRole('button', { name: /Próximo|Next/i });
      
      // Step 2 -> 3
      await nextBtn.click();
      await page.waitForTimeout(500);
      
      // Step 3 -> 4 (Plan)
      await nextBtn.click();
      await page.waitForTimeout(500);
      
      // Step 4 -> 5 (Trainer)
      await nextBtn.click();
      await page.waitForTimeout(500);
      
      // Step 5: Finish
      const finishBtn = page.getByRole('button', { name: /Finalizar|Finish|Concluir/i });
      await finishBtn.click();
      
      const goDashBtn = page.getByRole('button', { name: /Ir para o Dashboard|Go to Dashboard/i });
      await goDashBtn.click();
    }

    await expect(page).toHaveURL(/.*dashboard/, { timeout: 20000 });
  } catch (error) {
    console.warn('QA Warning: First login attempt failed, retrying...');
    
    // Check if there is an error message visible on the login page
    const errorText = await page.locator('p.text-red-500, [role="alert"]').allTextContents();
    console.log('QA: Login errors found:', errorText);
    
    if (errorText.length > 0) {
      // Re-fill password and submit if there was an error
      await page.locator('input[name="password"]').fill(password);
    }
    
    await page.waitForTimeout(2000);
    await submitBtn.click();
    
    try {
      await expect(page).toHaveURL(/.*dashboard/, { timeout: 15000 });
    } catch (finalError) {
      console.error('QA: FINAL LOGIN FAILED. Dumping page content and taking screenshot:');
      await page.screenshot({ path: 'playwright-report/login-failure.png' });
      console.log(await page.content());
      throw finalError;
    }
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
