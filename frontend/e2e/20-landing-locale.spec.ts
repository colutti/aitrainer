import { test, expect } from '@playwright/test';

test.describe('Landing Locale Switch', () => {
  test('switches the landing page between Portuguese, English, and Spanish', async ({ page }) => {
    await page.goto('/');

    const languageButton = page.getByRole('button', { name: /^PT$/ });
    await expect(languageButton).toBeVisible();
    await expect(page.getByRole('button', { name: 'Começar agora' })).toBeVisible();

    await languageButton.click();
    await page.getByRole('button', { name: /English/ }).click();
    await expect(page.getByRole('button', { name: /^EN$/ })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Start Journey' })).toBeVisible();

    await page.getByRole('button', { name: /^EN$/ }).click();
    await page.getByRole('button', { name: /Español/ }).click();
    await expect(page.getByRole('button', { name: /^ES$/ })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Empezar ahora' })).toBeVisible();
  });
});
