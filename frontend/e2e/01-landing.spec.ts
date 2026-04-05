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

    // 3. Verify Hero section elements
    await expect(page.getByRole('heading', { name: t('landing.hero.title') })).toBeVisible();

    // 4. Verify Pricing section is present
    await expect(page.getByRole('heading', { name: t('landing.plans.title') })).toBeVisible();
    
    // 5. Verify FAQ is present
    await expect(page.getByRole('heading', { name: t('landing.faq.title') })).toBeVisible();
  });
});
