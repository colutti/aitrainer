import { test, expect } from '@playwright/test';

test('SettingsPage mobile layout (375px)', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto('http://localhost:3000/settings/profile');

  // Wait for page load
  await page.waitForLoadState('networkidle');

  // Tabs should be visible
  const nav = page.locator('nav').first();
  await expect(nav).toBeVisible();

  // User info should be visible below (lg:hidden = visible on mobile)
  const userInfoMobile = page.locator('div.lg\\:hidden').last();
  await expect(userInfoMobile).toBeVisible();
});

test('SettingsPage desktop layout (1920px)', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 });
  await page.goto('http://localhost:3000/settings/profile');

  await page.waitForLoadState('networkidle');

  // Tabs visible
  const nav = page.locator('nav').first();
  await expect(nav).toBeVisible();

  // User info sidebar (hidden lg:block = visible on desktop)
  const userInfoSidebar = page.locator('div.hidden.lg\\:block').first();
  await expect(userInfoSidebar).toBeVisible();
});

test('SettingsPage 4K layout (3840px)', async ({ page }) => {
  await page.setViewportSize({ width: 3840, height: 2160 });
  await page.goto('http://localhost:3000/settings/profile');

  await page.waitForLoadState('networkidle');

  // Content area should not stretch excessively
  const contentArea = page.locator('div.lg\\:col-span-2');
  const box = await contentArea.boundingBox();

  // Col-span-2 in 3-col grid should be ~1280px max on 3840px viewport
  expect(box?.width).toBeLessThan(1500);
});
