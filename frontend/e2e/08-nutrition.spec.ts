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

    // Click the Action button which delegates to AI Chat
    const addButton = authenticatedPage.getByTestId('view-header-action').first();
    await addButton.click();

    // Verify redirection to chat
    await expect(authenticatedPage).toHaveURL(/.*chat/);
  });
});
