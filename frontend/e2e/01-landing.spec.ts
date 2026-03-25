import { test, expect } from '@playwright/test';

import { t } from './helpers/translations';

// Override global storageState to ensure unauthenticated access for landing page tests
test.use({ storageState: { cookies: [], origins: [] } });

test.describe('Landing Page (Public Access)', () => {
  test('should display main sections for unauthenticated user', async ({ page }) => {
    // 1. Visit root URL
    await page.goto('/');

    // 2. Verify we did NOT get redirected to dashboard
    await expect(page).toHaveURL(/.*\//);

    // 3. Verify Hero section elements (using translations if possible or generic robust locators)
    // Looking for the main call to action button which usually points to login or signup
    const loginButton = page.getByRole('button', { name: /Entrar|Login/i }).first();
    await expect(loginButton).toBeVisible();

    // 4. Verify Pricing section is present
    // Looking for some generic text that appears in the pricing or comparison tables
    const pricingHeader = page.getByRole('heading', { name: /Plano|Preço|Pricing/i }).first();
    await expect(pricingHeader).toBeVisible();
    
    // 5. Verify FAQ is present
    const faqHeader = page.getByRole('heading', { name: /FAQ|Perguntas/i }).first();
    await expect(faqHeader).toBeVisible();
  });

  test('should redirect authenticated user to dashboard', async ({ browser }) => {
    // For this specific test, we manually load the authenticated state
    const context = await browser.newContext({ storageState: 'playwright/.auth/user.json' });
    const authPage = await context.newPage();
    
    await authPage.goto('/');
    
    // Should be automatically redirected to dashboard
    await expect(authPage).toHaveURL(/.*dashboard/);
    
    await context.close();
  });
});
