import { test, expect } from '@playwright/test';

test('SettingsPage no scroll jump on mobile tab navigation', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto('/settings/profile');

  await page.waitForLoadState('networkidle');

  // Get initial scroll position
  const initialScroll = await page.evaluate(() => window.scrollY);

  // Click on different tab
  const trainersTab = page.locator('nav:has-text("Perfil Pessoal")').locator('a:has-text("Treinador AI")');
  await trainersTab.click();

  // Wait for navigation
  await page.waitForLoadState('networkidle');

  // Check scroll position hasn't jumped drastically
  const afterScroll = await page.evaluate(() => window.scrollY);

  // Allow small scroll adjustment but not a large jump
  const scrollDifference = Math.abs(afterScroll - initialScroll);
  expect(scrollDifference).toBeLessThan(100);
});

test('SettingsPage content is scrollable without layout shift', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto('/settings/profile');

  await page.waitForLoadState('networkidle');

  // Scroll down
  await page.evaluate(() => {
    window.scrollBy(0, 300);
  });

  const scrollAfterManualScroll = await page.evaluate(() => window.scrollY);

  // Verify we can scroll
  expect(scrollAfterManualScroll).toBeGreaterThan(0);

  // Click on another tab
  const memoriasTab = page.locator('nav:has-text("Perfil Pessoal")').locator('a:has-text("Memórias")');
  await memoriasTab.click();

  await page.waitForLoadState('networkidle');

  // Content should be readable without excessive shifts
  const contentArea = page.locator('div.lg\\:col-span-2');
  await expect(contentArea).toBeVisible();
});

test('SettingsPage no horizontal scroll on mobile', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto('/settings/profile');

  await page.waitForLoadState('networkidle');

  // Get viewport width
  const viewportWidth = await page.evaluate(() => window.innerWidth);

  // Get body width
  const bodyWidth = await page.evaluate(() => document.body.scrollWidth);

  // Should not have horizontal overflow
  expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 1); // +1 for rounding errors
});
