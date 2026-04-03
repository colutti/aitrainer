import { test, expect } from '@playwright/test';

test.describe('Landing Locale Switch', () => {
  test('switches the landing page between Portuguese, English, and Spanish', async ({ page }) => {
    await page.goto('/');

    const ensureLanguageButtonVisible = async (shortCode: 'PT' | 'EN' | 'ES') => {
      const languageButton = page.getByRole('button', { name: new RegExp(`^${shortCode}$`) }).first();
      if (await languageButton.isVisible().catch(() => false)) {
        return languageButton;
      }

      const mobileMenuToggle = page.getByRole('button', { name: /toggle menu/i });
      if (await mobileMenuToggle.isVisible().catch(() => false)) {
        await mobileMenuToggle.click();
        await expect(languageButton).toBeVisible({ timeout: 10000 });
        return languageButton;
      }

      throw new Error(`Language button ${shortCode} is not visible`);
    };

    const languageButton = await ensureLanguageButtonVisible('PT');
    await expect(languageButton).toBeVisible();
    await expect(page.getByRole('button', { name: 'Começar agora' })).toBeVisible();

    await languageButton.click();
    await page.getByRole('button', { name: /English/ }).click();
    await expect(await ensureLanguageButtonVisible('EN')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Start Journey' })).toBeVisible();

    await (await ensureLanguageButtonVisible('EN')).click();
    await page.getByRole('button', { name: /Español/ }).click();
    await expect(await ensureLanguageButtonVisible('ES')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Empezar ahora' })).toBeVisible();
  });
});
