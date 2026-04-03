import { test, expect } from '@playwright/test';

import { loginDemoUserViaUi } from './helpers/bootstrap';

// Override global storageState to ensure unauthenticated access for landing page tests
test.use({ storageState: { cookies: [], origins: [] } });

test.describe('Landing Page (Public Access)', () => {
  test('should display main sections for unauthenticated user', async ({ page }) => {
    // 1. Visit root URL
    await page.goto('/');

    // 2. Verify we did NOT get redirected to dashboard
    await expect(page).toHaveURL(/.*\//);

    // 3. Verify Hero section elements
    await expect(
      page.getByRole('heading', {
        name: /Seu Treinador IA Pessoal|Your AI Personal Trainer|Tu entrenador personal con IA/i,
      })
    ).toBeVisible();

    // 4. Verify Pricing section is present
    // Looking for some generic text that appears in the pricing or comparison tables
    const pricingHeader = page.getByRole('heading', { name: /Plano|Preço|Pricing/i }).first();
    await expect(pricingHeader).toBeVisible();
    
    // 5. Verify FAQ is present
    const faqHeader = page.getByRole('heading', { name: /FAQ|Perguntas/i }).first();
    await expect(faqHeader).toBeVisible();
  });

  test('should redirect authenticated user to dashboard', async ({ browser }) => {
    const context = await browser.newContext();
    const authPage = await context.newPage();
    await loginDemoUserViaUi(authPage);
    await authPage.goto('/');
    await expect(authPage).toHaveURL(/.*dashboard/);
    await context.close();
  });
});
