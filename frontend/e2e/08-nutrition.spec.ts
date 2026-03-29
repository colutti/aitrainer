import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Nutrition Feature', () => {
  test('should verify nutrition page elements and empty state', async ({ authenticatedPage, ui }) => {
    // 1. Navigate to Body View
    await ui.navigateTo('body');

    // 2. Switch to Nutrition Tab
    await ui.switchToTab(t('body.nutrition_title'));

    // 3. Verify Empty State or Action button
    const addButton = authenticatedPage.getByTestId('view-header-action').first();
    await expect(addButton).toBeVisible({ timeout: 10000 });
  });

  test('should redirect to chat when clicking to register meal', async ({ authenticatedPage, ui }) => {
    await ui.navigateTo('body');
    await ui.switchToTab(t('body.nutrition_title'));

    const addButton = authenticatedPage.getByTestId('view-header-action').first();
    await addButton.click();

    await expect(authenticatedPage).toHaveURL(/.*chat/);
    await expect(authenticatedPage.getByTestId('chat-form')).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByTestId('chat-input')).toBeVisible({ timeout: 15000 });
  });

  test('should persist a nutrition log after the chat handoff', async ({ authenticatedPage, ui, api }) => {
    await ui.navigateTo('body');
    await ui.switchToTab(t('body.nutrition_title'));

    await authenticatedPage.getByTestId('view-header-action').first().click();
    await expect(authenticatedPage).toHaveURL(/.*chat/);
    await expect(authenticatedPage.getByTestId('chat-input')).toBeVisible({ timeout: 15000 });

    const calories = 612;
    const protein = 41;
    const carbs = 72;
    const fat = 19;
    const date = new Date().toISOString().split('T')[0];

    await api.post('/nutrition/log', {
      data: {
        date,
        source: 'Manual E2E',
        calories,
        protein_grams: protein,
        carbs_grams: carbs,
        fat_grams: fat,
      },
    });

    const response = await api.get('/nutrition/list?page=1&page_size=20');
    expect(response.status()).toBe(200);
    const payload = await response.json() as { logs?: { calories?: number }[] };
    expect(payload.logs?.some((log) => log.calories === calories)).toBe(true);

    await ui.navigateTo('body');
    await ui.switchToTab(t('body.nutrition_title'));
    await authenticatedPage.waitForTimeout(1000);
    const nutritionCard = authenticatedPage.getByTestId('nutrition-log-card').first();
    await expect(nutritionCard).toBeVisible({ timeout: 15000 });
    await expect(nutritionCard).toContainText(/kcal/i);

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await expect(nutritionCard).toBeVisible({ timeout: 15000 });
  });
});
