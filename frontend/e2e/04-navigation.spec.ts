import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Navigation Flow', () => {
  test('should navigate correctly between main pages', async ({ authenticatedPage, ui }) => {
    // 1. Navigate to Workouts
    await ui.navigateTo('workouts');
    await expect(authenticatedPage).toHaveURL(/.*workouts/);
    await expect(authenticatedPage.getByTestId('workouts-list-screen')).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByTestId('page-header-title')).toContainText(t('workouts.title'));

    // 2. Navigate to Chat
    await ui.navigateTo('chat');
    await expect(authenticatedPage).toHaveURL(/.*chat/);

    // 3. Navigate to Body
    await ui.navigateTo('body');
    await expect(authenticatedPage).toHaveURL(/.*body/);
    await expect(authenticatedPage.getByTestId('body-insight-screen')).toBeVisible({ timeout: 15000 });
    await expect(
      authenticatedPage.getByRole('button', { name: /Registrar Peso|Register Weight|Registrar Peso/i }),
    ).toBeVisible({ timeout: 15000 });

    // 4. Navigate to Nutrition
    await authenticatedPage.goto('/dashboard/nutrition', { waitUntil: 'networkidle' });
    await expect(authenticatedPage).toHaveURL(/.*nutrition/);
    await expect(
      authenticatedPage.getByRole('button', { name: /Registrar Refei..o|Register Meal|Registrar Comida/i }),
    ).toBeVisible({ timeout: 15000 });

    // 5. Navigate back to Home
    await ui.navigateTo('home');
    await expect(authenticatedPage).toHaveURL(/.*dashboard/);
  });

  test('should show correct subscription badge in Navigation', async ({ authenticatedPage }) => {
    const freeBadges = authenticatedPage.getByText('Free', { exact: true });
    await expect(freeBadges.first()).toBeAttached();
  });
});
