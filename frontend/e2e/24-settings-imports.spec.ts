import type { APIRequestContext } from '@playwright/test';

import { test, expect } from './fixtures';
import { bootstrapOnboardedUser } from './helpers/bootstrap';
import { loadImportFixture } from './helpers/import-fixtures';
import { t } from './helpers/translations';

function replacements() {
  const today = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().split('T')[0];
  const yesterday = new Date(Date.now()).toISOString().split('T')[0];
  return {
    '{{TODAY}}': today,
    '{{YESTERDAY}}': yesterday,
  };
}

async function uploadImport(page: import('@playwright/test').Page, index: number, kind: 'mfp' | 'zepp') {
  await page.locator('input[type="file"]').nth(index).setInputFiles(loadImportFixture(kind, replacements()));
}

async function createAuthedApi(page: import('@playwright/test').Page, playwright: { request: { newContext: (options: {
  baseURL: string;
  extraHTTPHeaders: Record<string, string>;
}) => Promise<APIRequestContext>; } }) {
  const token = await page.evaluate(() => localStorage.getItem('auth_token') ?? '');

  return playwright.request.newContext({
    baseURL: process.env.E2E_API_BASE_URL ?? 'http://localhost:8000',
    extraHTTPHeaders: {
      Authorization: token ? `Bearer ${token}` : '',
    },
  });
}

async function getImportTotals(api: APIRequestContext) {
  const [nutritionResponse, weightResponse] = await Promise.all([
    api.get('/nutrition/list?page_size=50'),
    api.get('/weight?page_size=100'),
  ]);

  expect(nutritionResponse.ok()).toBeTruthy();
  expect(weightResponse.ok()).toBeTruthy();

  const nutritionPayload = (await nutritionResponse.json()) as { total: number };
  const weightPayload = (await weightResponse.json()) as { total: number };

  return {
    nutritionTotal: nutritionPayload.total,
    weightTotal: weightPayload.total,
  };
}

test.describe('Settings imports', () => {
  test('imports MyFitnessPal CSV and reflects nutrition on body and dashboard', async ({ page, playwright }, testInfo) => {
    test.setTimeout(120000);

    const authenticatedPage = await bootstrapOnboardedUser(page, testInfo, {
      subscriptionPlan: 'Pro',
    });
    const api = await createAuthedApi(authenticatedPage, playwright);

    await authenticatedPage.goto('/dashboard/settings/integrations');
    await authenticatedPage.waitForLoadState('networkidle');

    await uploadImport(authenticatedPage, 0, 'mfp');

    await authenticatedPage.goto('/dashboard/nutrition');
    await authenticatedPage.waitForLoadState('networkidle');
    await expect(authenticatedPage.getByTestId('nutrition-log-card').first()).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByTestId('nutrition-log-card').first()).toContainText(/900/);
    await expect(authenticatedPage.getByTestId('nutrition-log-card').first()).toContainText(/71g/);

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await authenticatedPage.goto('/dashboard/nutrition');
    await authenticatedPage.waitForLoadState('networkidle');
    await expect(authenticatedPage.getByTestId('nutrition-log-card').first()).toBeVisible({ timeout: 15000 });

    await authenticatedPage.goto('/dashboard');
    await authenticatedPage.waitForLoadState('networkidle');
    await expect(authenticatedPage.getByTestId('dashboard-bento')).toBeVisible({ timeout: 20000 });
    await expect(authenticatedPage.getByTestId('dashboard-bento')).toContainText(/900/);
    await api.dispose();
  });

  test('rejects an invalid MyFitnessPal CSV without persisting changes', async ({ page, ui, playwright }, testInfo) => {
    test.setTimeout(120000);

    const authenticatedPage = await bootstrapOnboardedUser(page, testInfo, {
      subscriptionPlan: 'Pro',
    });
    const api = await createAuthedApi(authenticatedPage, playwright);
    const beforeTotals = await getImportTotals(api);

    await authenticatedPage.goto('/dashboard/settings/integrations');
    await authenticatedPage.waitForLoadState('networkidle');

    await authenticatedPage.locator('input[type="file"]').nth(0).setInputFiles({
      name: 'invalid-myfitnesspal.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from('Data,Calorias\n2026-06-28,123\n', 'utf-8'),
    });

    await ui.waitForToast('settings.integrations.imports.error');

    const afterTotals = await getImportTotals(api);
    expect(afterTotals).toEqual(beforeTotals);
    await expect(authenticatedPage.getByText(t('settings.integrations.imports.error'))).toBeVisible();
    await api.dispose();
  });

  test('imports Zepp Life CSV and reflects weight on body and dashboard', async ({ page, playwright }, testInfo) => {
    test.setTimeout(120000);

    const authenticatedPage = await bootstrapOnboardedUser(page, testInfo, {
      subscriptionPlan: 'Pro',
    });
    const api = await createAuthedApi(authenticatedPage, playwright);

    await authenticatedPage.goto('/dashboard/settings/integrations');
    await authenticatedPage.waitForLoadState('networkidle');

    await uploadImport(authenticatedPage, 1, 'zepp');

    await authenticatedPage.goto('/dashboard/body');
    await authenticatedPage.waitForLoadState('networkidle');
    const importedWeightCard = authenticatedPage.getByTestId('weight-log-card').filter({ hasText: '82.4' }).first();
    await expect(importedWeightCard).toBeVisible({ timeout: 15000 });
    await expect(importedWeightCard).toContainText('18.2');

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await authenticatedPage.goto('/dashboard/body');
    await authenticatedPage.waitForLoadState('networkidle');
    await expect(authenticatedPage.getByTestId('weight-log-card').filter({ hasText: '82.4' }).first()).toBeVisible({
      timeout: 15000,
    });

    await authenticatedPage.goto('/dashboard');
    await authenticatedPage.waitForLoadState('networkidle');
    await expect(authenticatedPage.getByTestId('dashboard-bento')).toContainText('82.4');
    await expect(authenticatedPage.getByTestId('widget-metabolism')).toBeVisible({ timeout: 15000 });
    await api.dispose();
  });
});
