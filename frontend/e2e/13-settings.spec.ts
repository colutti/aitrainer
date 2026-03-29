import { test, expect } from './fixtures';

test.describe('General Settings', () => {
  test('locks premium trainers for free users and redirects to subscription', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/settings/trainer');
    await authenticatedPage.waitForLoadState('networkidle');

    const gymbroCard = authenticatedPage.getByTestId('trainer-card-gymbro').first();
    const atlasCard = authenticatedPage.getByTestId('trainer-card-atlas').first();

    await expect(gymbroCard).toBeVisible({ timeout: 15000 });
    await expect(atlasCard).toBeVisible();
    await expect(gymbroCard.getByTestId('check-icon')).toBeVisible();
    await expect(atlasCard.getByTestId('lock-icon')).toBeVisible();

    await atlasCard.click();
    await expect(authenticatedPage).toHaveURL(/.*settings\/subscription/);
  });
});
