import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Weight Tracking Feature', () => {
  test('should verify weight page elements and register a new weight', async ({ authenticatedPage, ui }) => {
    // 1. Navigate to Body
    await ui.navigateTo('body');

    // 2. Verify Page Title
    await expect(authenticatedPage.getByTestId('view-header-title')).toContainText(t('body.weight.history_title'));

    // 3. Open Register Weight Drawer
    await ui.openDrawer(t('body.weight.register_weight'));

    // 4. Fill Weight Data
    const newWeight = 78.5;
    const newFat = 18.2;
    
    await ui.fillForm({
      [t('body.weight.weight')]: newWeight,
      [t('body.weight.body_fat')]: newFat
    });

    // 5. Submit
    await ui.submit();

    // 6. Verify Drawer Closed
    await expect(authenticatedPage.getByRole('heading', { name: t('body.weight.register_weight') })).toBeHidden({ timeout: 15000 });

    // 7. Verify Data in List
    const weightCard = authenticatedPage.locator('div').filter({ hasText: String(newWeight) }).first();
    await expect(weightCard).toBeVisible({ timeout: 10000 });
  });

  test('should verify weight trend in dashboard after logging', async ({ authenticatedPage, ui }) => {
    await ui.navigateTo('dashboard');
    
    // Look for the weight widget in bento
    const weightWidget = authenticatedPage.getByTestId('dashboard-bento').locator('div').filter({ hasText: t('dashboard.chart.weight') }).first();
    await expect(weightWidget).toBeVisible();
    
    // Verify weight value is present
    const weightValue = weightWidget.locator('span').filter({ hasText: /\d+/ }).first();
    await expect(weightValue).not.toBeEmpty();
  });
});
