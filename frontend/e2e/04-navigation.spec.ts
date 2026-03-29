import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Navigation Flow', () => {
  test('should navigate correctly between main pages', async ({ authenticatedPage, ui }) => {
    // 1. Navigate to Workouts
    await ui.navigateTo('workouts');
    await expect(authenticatedPage).toHaveURL(/.*workouts/);
    await expect(authenticatedPage.getByTestId('view-header-title')).toContainText(t('workouts.title'));

    // 2. Navigate to Chat
    await ui.navigateTo('chat');
    await expect(authenticatedPage).toHaveURL(/.*chat/);

    // 3. Navigate to Body (Integrated View)
    await ui.navigateTo('body');
    await expect(authenticatedPage).toHaveURL(/.*body/);
    
    // Check Tabs in Body View
    const weightTabTitle = t('body.weight_title');
    const nutritionTabTitle = t('body.nutrition_title');
    
    await expect(authenticatedPage.getByRole('button', { name: weightTabTitle })).toBeVisible();
    await ui.switchToTab(nutritionTabTitle);
    await expect(authenticatedPage.getByRole('button', { name: nutritionTabTitle })).toBeVisible();
    await expect(authenticatedPage.getByTestId('body-tab-nutrition')).toBeVisible();

    // 4. Navigate back to Home
    await ui.navigateTo('home');
    await expect(authenticatedPage).toHaveURL(/.*dashboard/);
  });

  test('should show correct subscription badge in Navigation', async ({ authenticatedPage }) => {
    const freeBadges = authenticatedPage.getByText('Free', { exact: true });
    await expect(freeBadges.first()).toBeAttached();
  });
});
