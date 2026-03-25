import { test, expect } from './fixtures';
import { cleanupUserData } from './helpers/cleanup';

test.describe('General Settings', () => {

  test.beforeEach(async ({ api }) => {
    await cleanupUserData(api);
  });

  test('should verify trainer is locked to GymBro for Free users', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/settings/trainer');
    await authenticatedPage.waitForLoadState('networkidle');

    // On Free plan, GymBro is the only available trainer. Atlas should have a lock icon.
    const brenoCard = authenticatedPage.getByTestId('trainer-card-gymbro').first();
    const atlasCard = authenticatedPage.getByTestId('trainer-card-atlas').first();

    await expect(brenoCard).toBeVisible({ timeout: 15000 });
    await expect(atlasCard).toBeVisible();

    // Check lock icon exists on Atlas
    await expect(atlasCard.getByTestId('lock-icon')).toBeVisible();

    // GymBro should be selected by default for new Free users
    await expect(brenoCard.getByTestId('check-icon')).toBeVisible();

    // Clicking Atlas should NOT change selection (it redirects or does nothing depending on implementation)
    // In our Premium UI, it redirects to subscription
    await atlasCard.click();
    await expect(authenticatedPage).toHaveURL(/.*subscription/);
  });

  test('should show correct subscription info', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/settings/subscription');
    await authenticatedPage.waitForLoadState('networkidle');

    // The Free plan is localized to "Gratuito" or "Free"
    await expect(authenticatedPage.getByText(/Gratuito|Free/i).first()).toBeVisible({ timeout: 15000 });
  });
});
