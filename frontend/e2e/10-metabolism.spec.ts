import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Metabolism Features', () => {
  test('should reflect a fresh weight log on the dashboard after reload', async ({ authenticatedPage, ui }) => {
    await ui.navigateTo('body');
    await ui.openDrawer(t('body.weight.register_weight'));

    const newWeight = 73.4;
    const newFat = 17.6;
    const tomorrow = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    await authenticatedPage.locator('form input[type="hidden"]').last().evaluate((element, value) => {
      const input = element as HTMLInputElement;
      input.value = String(value);
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }, tomorrow);
    await ui.fillForm({
      [t('body.weight.weight')]: newWeight,
      [t('body.weight.body_fat')]: newFat,
    });
    await authenticatedPage.getByLabel(t('body.weight.notes')).fill(`metabolism-e2e-${Date.now()}`);
    await ui.submit();
    await expect(authenticatedPage.getByTestId('weight-log-card').filter({ hasText: String(newWeight) }).first()).toBeVisible({ timeout: 15000 });

    await ui.navigateTo('dashboard');
    await expect(authenticatedPage.getByTestId('widget-metabolism')).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByTestId('widget-metabolism')).toContainText(/\d{4}/);
    await expect(authenticatedPage.getByTestId('dashboard-bento')).toContainText(String(newWeight));

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await expect(authenticatedPage.getByTestId('widget-metabolism')).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByTestId('dashboard-bento')).toContainText(String(newWeight));
  });
});
