import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('UI Components & Utilities', () => {
  test('should open Quick Add FAB and verify options', async ({ authenticatedPage }) => {
    // Navigate to dashboard where FAB is visible
    await authenticatedPage.goto('/dashboard');

    // 1. Find and click the Floating Action Button (FAB)
    const fabButton = authenticatedPage.getByTestId('quick-add-fab');
    await expect(fabButton).toBeVisible();
    await fabButton.click();

    // 2. Wait for the menu to expand and check options
    const weightOption = authenticatedPage.getByText(t('body.weight.register_weight'));
    const mealOption = authenticatedPage.getByText(t('body.nutrition.register_title'));
    const workoutOption = authenticatedPage.getByText(t('workouts.register_workout'));

    await expect(weightOption).toBeVisible({ timeout: 10000 });
    await expect(mealOption).toBeVisible({ timeout: 10000 });
    await expect(workoutOption).toBeVisible({ timeout: 10000 });

    // 3. Click the FAB again to close it (Toggle behavior)
    // Using force: true because the button might be slightly rotated or transitioning
    await fabButton.click({ force: true });
    
    // 4. Verify options are hidden
    await expect(weightOption).toBeHidden({ timeout: 10000 });
    await expect(mealOption).toBeHidden({ timeout: 10000 });
    await expect(workoutOption).toBeHidden({ timeout: 10000 });
  });
});
