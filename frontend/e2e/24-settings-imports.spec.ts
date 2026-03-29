import { test, expect } from './fixtures';
import { loadImportFixture } from './helpers/import-fixtures';

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

test.describe('Settings imports', () => {
  test('imports MyFitnessPal CSV and reflects nutrition on body and dashboard', async ({ authenticatedPage, ui }) => {
    test.setTimeout(120000);

    await authenticatedPage.goto('/dashboard/settings/integrations');
    await authenticatedPage.waitForLoadState('networkidle');

    await uploadImport(authenticatedPage, 0, 'mfp');

    await authenticatedPage.goto('/dashboard/body');
    await authenticatedPage.waitForLoadState('networkidle');
    await ui.switchToTab('Dieta & Macros');
    await expect(authenticatedPage.getByTestId('nutrition-log-card').first()).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByTestId('nutrition-log-card').first()).toContainText(/900/);
    await expect(authenticatedPage.getByTestId('nutrition-log-card').first()).toContainText(/71g/);

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await authenticatedPage.goto('/dashboard/body');
    await authenticatedPage.waitForLoadState('networkidle');
    await ui.switchToTab('Dieta & Macros');
    await expect(authenticatedPage.getByTestId('nutrition-log-card').first()).toBeVisible({ timeout: 15000 });

    await authenticatedPage.goto('/dashboard');
    await authenticatedPage.waitForLoadState('networkidle');
    await expect(authenticatedPage.getByTestId('dashboard-bento')).toBeVisible({ timeout: 20000 });
    await expect(authenticatedPage.getByTestId('dashboard-bento')).toContainText(/900/);
  });

  test('imports Zepp Life CSV and reflects weight on body and dashboard', async ({ authenticatedPage, ui }) => {
    test.setTimeout(120000);

    await authenticatedPage.goto('/dashboard/settings/integrations');
    await authenticatedPage.waitForLoadState('networkidle');

    await uploadImport(authenticatedPage, 1, 'zepp');

    await authenticatedPage.goto('/dashboard/body');
    await authenticatedPage.waitForLoadState('networkidle');
    await ui.switchToTab('Peso & Composição');
    const importedWeightCard = authenticatedPage.getByTestId('weight-log-card').filter({ hasText: '82.4' }).first();
    await expect(importedWeightCard).toBeVisible({ timeout: 15000 });
    await expect(importedWeightCard).toContainText('18.2');

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await authenticatedPage.goto('/dashboard/body');
    await authenticatedPage.waitForLoadState('networkidle');
    await ui.switchToTab('Peso & Composição');
    await expect(authenticatedPage.getByTestId('weight-log-card').filter({ hasText: '82.4' }).first()).toBeVisible({
      timeout: 15000,
    });

    await authenticatedPage.goto('/dashboard');
    await authenticatedPage.waitForLoadState('networkidle');
    await expect(authenticatedPage.getByTestId('dashboard-bento')).toContainText('82.4');
    await expect(authenticatedPage.getByTestId('widget-metabolism')).toBeVisible({ timeout: 15000 });
  });
});
