import * as path from 'path';

import { test, expect } from '@playwright/test';

// Disable auth.setup for this test so we are unauthenticated and can use the invite token
test.use({ storageState: { cookies: [], origins: [] } });

test('onboarding exploratory test', async ({ page }) => {
  test.setTimeout(60000);
  console.log("Navigating to onboarding...");
  await page.goto('http://localhost:3000/onboarding?token=a3bc0786-b15a-463c-8d0b-7678b69ddda3');
  
  await page.waitForTimeout(2000); // let it load
  await page.screenshot({ path: path.join('e2e-screenshots', '1_onboarding_start.png') });
  
  // Step 1: Info
  const inputs = page.locator('input');
  const count = await inputs.count();
  console.log(`Found ${count} inputs on step 1`);

  // Fill based on what's available
  await page.getByPlaceholder(/idade/i).fill('30', { timeout: 2000 }).catch(() => {});
  await page.getByPlaceholder(/peso/i).fill('80', { timeout: 2000 }).catch(() => {});
  await page.getByPlaceholder(/altura/i).fill('180', { timeout: 2000 }).catch(() => {});
  
  await page.screenshot({ path: path.join('e2e-screenshots', '2_onboarding_step1_filled.png') });
  await page.click('button:has-text("Próximo")', { timeout: 2000 }).catch(() => {});
  await page.waitForTimeout(1000);
  
  // Step 2: Goal
  await page.locator('.border-gradient-start').first().click({ timeout: 2000 }).catch(() => {});
  await page.screenshot({ path: path.join('e2e-screenshots', '3_onboarding_step2.png') });
  await page.click('button:has-text("Próximo")', { timeout: 2000 }).catch(() => {});
  await page.waitForTimeout(1000);

  // Step 3: Trainer & Password
  await page.fill('input[type="password"]', 'Let7hu118', { timeout: 2000 }).catch(() => {});
  await page.screenshot({ path: path.join('e2e-screenshots', '4_onboarding_step3_filled.png') });
  await page.click('button:has-text("Concluir")', { timeout: 2000 }).catch(() => {});
  await page.waitForTimeout(4000);
  
  // Success Screen
  await page.screenshot({ path: path.join('e2e-screenshots', '5_onboarding_success.png') });
  await page.click('button:has-text("Dashboard")', { timeout: 2000 }).catch(() => {});
  await page.click('button:has-text("Ir para o Dashboard")', { timeout: 2000 }).catch(() => {});
  
  await page.waitForURL('**/dashboard', { timeout: 10000 }).catch(() => {});
  await page.waitForTimeout(3000);
  
  // Dashboard & Tour
  await page.screenshot({ path: path.join('e2e-screenshots', '6_dashboard_tour.png') });
  
  // Click next on tour if visible
  const nextTourButton = page.locator('button:has-text("Próximo")');
  if (await nextTourButton.isVisible().catch(() => false)) {
    await nextTourButton.click();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join('e2e-screenshots', '7_dashboard_tour_step2.png') });
  }

  // QuickAdd FAB
  await page.locator('.fixed.bottom-24 button.bg-gradient-start').first().click({ timeout: 2000 }).catch(() => {});
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join('e2e-screenshots', '8_dashboard_fab.png') });
});
