import fs from 'node:fs';

import { test as base, expect, type Page, type APIRequestContext } from '@playwright/test';

import { cleanupUserData, resetOnboarding } from './helpers/cleanup';
import { UIActions } from './helpers/ui-actions';

interface Fixtures {
  api: APIRequestContext;
  ui: UIActions;
  authenticatedPage: Page;
  freshUser: Page;
  seedMemory: (text: string) => Promise<void>;
}

/**
 * Premium E2E Fixtures (ULTRA STABLE REAL EDITION)
 */
export const test = base.extend<Fixtures>({
  // UI Actions Helper (POM)
  ui: async ({ page }, use) => {
    const ui = new UIActions(page);
    await use(ui);
  },

  // API Fixture - Independent of any page navigation
  api: async ({ playwright }, use) => {
    // 1. Get Firebase ID Token (Simulated or Real depending on backend mode)
    // For now, since we are in "real" mode, we might need to actually perform a login 
    // but the backend Hybrid mode allows bypass if configured or we use the platform JWT if we had it.
    // However, the easiest way to get a FRESH platform token is to use the login endpoint.
    
    // Since we already have storageState from auth.setup.ts, we can try to extract the token from it
    const authState = JSON.parse(fs.readFileSync('playwright/.auth/user.json', 'utf-8'));
    const token = authState.origins[0]?.localStorage.find((i: any) => i.name === 'auth_token')?.value;

    const apiContext = await playwright.request.newContext({
      baseURL: 'http://localhost:8000',
      extraHTTPHeaders: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    await use(apiContext);

    // After test cleanup
    await cleanupUserData(apiContext);
    await apiContext.dispose();
  },

  // Helper to seed a memory
  seedMemory: async ({ api }, use) => {
    const fn = async (text: string) => {
      await api.post('/memory', {
        data: { memory: text }
      });
    };
    await use(fn);
  },

  // Authenticated Page Fixture
  authenticatedPage: async ({ page }, use) => {
    // 1. Force Desktop Viewport
    await page.setViewportSize({ width: 1280, height: 720 });

    // 2. Navigate to Dashboard
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // If we landed on onboarding, it means the user state was left incomplete by a previous failed test
    if (page.url().includes('/onboarding')) {
      console.log('QA: Landed on Onboarding in fixture, attempting minimal completion...');

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

      await expect(page).toHaveURL(/.*dashboard/, { timeout: 20000 });
    }


    // 4. WAIT for Premium Animations and Hydration
    await expect(page.getByTestId('desktop-nav').or(page.getByTestId('mobile-nav')).first()).toBeVisible({ timeout: 20000 });
    await page.waitForTimeout(3000); 

    await use(page);
  },

  // Fixture for a user that needs to go through onboarding
  freshUser: async ({ browser, api }, use) => {
    // 1. Reset user state to require onboarding BEFORE opening any page
    await resetOnboarding(api);
    
    // 2. Open page with existing auth
    const context = await browser.newContext({ storageState: 'playwright/.auth/user.json' });
    const page = await context.newPage();
    
    // 3. Navigate to root or dashboard - should redirect to onboarding
    await page.goto('/dashboard');
    
    await use(page);
    
    await page.close();
    await context.close();
  }
});

export { expect };
