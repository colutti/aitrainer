import { test, expect } from './fixtures';
import { bootstrapOnboardedUser } from './helpers/bootstrap';
import { t } from './helpers/translations';

test.describe('General Settings', () => {
  test('locks premium trainers for free users and redirects to subscription', async ({ page }, testInfo) => {
    const authenticatedPage = await bootstrapOnboardedUser(page, testInfo);

    await authenticatedPage.goto('/dashboard/settings/trainer');
    await authenticatedPage.waitForLoadState('networkidle');

    const gymbroCard = authenticatedPage.getByTestId('trainer-card-gymbro').first();
    const atlasCard = authenticatedPage.getByTestId('trainer-card-atlas').first();

    await expect(gymbroCard).toBeVisible({ timeout: 15000 });
    await expect(atlasCard).toBeVisible();
    await expect(gymbroCard.getByTestId('check-icon')).toBeVisible();
    await expect(atlasCard.getByTestId('lock-icon')).toBeVisible();

    await atlasCard.click({ force: true });
    await expect(authenticatedPage).toHaveURL(/.*settings\/subscription/);
  });

  test('persists trainer selection changes for a pro user', async ({ page }, testInfo) => {
    const authenticatedPage = await bootstrapOnboardedUser(page, testInfo, {
      subscriptionPlan: 'Pro',
    });

    await authenticatedPage.goto('/dashboard/settings/trainer');
    await authenticatedPage.waitForLoadState('networkidle');

    const gymbroCard = authenticatedPage.getByTestId('trainer-card-gymbro').first();
    const atlasCard = authenticatedPage.getByTestId('trainer-card-atlas').first();

    await atlasCard.click();
    await authenticatedPage.getByRole('button', { name: t('settings.trainer.save_button') }).click();
    await expect(atlasCard.getByTestId('check-icon')).toBeVisible({ timeout: 15000 });

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await authenticatedPage.goto('/dashboard/settings/trainer');
    await authenticatedPage.waitForLoadState('networkidle');
    await expect(authenticatedPage.getByTestId('trainer-card-atlas').first().getByTestId('check-icon')).toBeVisible({
      timeout: 15000,
    });

    await authenticatedPage.getByTestId('trainer-card-gymbro').first().click({ force: true });
    await authenticatedPage.getByRole('button', { name: t('settings.trainer.save_button') }).click();
    await expect(authenticatedPage.getByTestId('trainer-card-gymbro').first().getByTestId('check-icon')).toBeVisible({
      timeout: 15000,
    });

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await authenticatedPage.goto('/dashboard/settings/trainer');
    await authenticatedPage.waitForLoadState('networkidle');
    await expect(authenticatedPage.getByTestId('trainer-card-gymbro').first().getByTestId('check-icon')).toBeVisible({
      timeout: 15000,
    });
  });
});
