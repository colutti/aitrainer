import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Weight Tracking Feature', () => {
  test('should register a new weight and keep it after reload', async ({ authenticatedPage, ui }) => {
    await ui.navigateTo('body');
    await expect(authenticatedPage.getByTestId('view-header-title')).toContainText(t('body.weight.history_title'));
    await ui.openDrawer(t('body.weight.register_weight'));

    const newWeight = 78.5;
    const newFat = 18.2;
    const notes = `E2E weight note ${Date.now()}`;

    await ui.fillForm({
      [t('body.weight.weight')]: newWeight,
      [t('body.weight.body_fat')]: newFat,
    });
    await authenticatedPage.getByLabel(t('body.weight.notes')).fill(notes);

    await ui.submit();
    await expect(authenticatedPage.getByRole('heading', { name: t('body.weight.register_weight') })).toBeHidden({ timeout: 15000 });
    const weightCard = authenticatedPage.getByTestId('weight-log-card').filter({ hasText: String(newWeight) }).filter({ hasText: notes }).first();
    await expect(weightCard).toBeVisible({ timeout: 10000 });

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await ui.navigateTo('body');
    const persistedCard = authenticatedPage.getByTestId('weight-log-card').filter({ hasText: String(newWeight) }).first();
    await expect(persistedCard).toBeVisible({ timeout: 15000 });

    await persistedCard.click();
    await expect(authenticatedPage.getByRole('heading', { name: t('body.weight.record_details') })).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByTestId('weight-kg')).toHaveValue(String(newWeight));
    await expect(authenticatedPage.getByTestId('body-fat-pct')).toHaveValue(String(newFat));
    await expect(authenticatedPage.locator('#notes')).toHaveValue(notes);
  });
});
