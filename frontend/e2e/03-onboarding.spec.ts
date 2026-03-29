import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Onboarding Flow (Manual)', () => {
  test('should complete onboarding flow', async ({ freshUser: page }) => {
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('pageerror', err => console.log('PAGE ERROR:', err.message));

    const stepTitle = page.getByText(t('onboarding.step_2_title'));
    await expect(stepTitle).toBeVisible({ timeout: 15000 });

    // Fill Profile
    await page.getByRole('button', { name: t('onboarding.genders.male'), exact: true }).click();
    await page.getByTestId('onboarding-name').fill('E2E Manual User');
    await page.getByTestId('onboarding-age').fill('30');
    await page.getByTestId('onboarding-height').fill('180');
    await page.getByTestId('onboarding-weight').fill('80');

    await page.getByRole('button', { name: t('onboarding.next') }).click();

    await expect(page.getByText(t('onboarding.step_plan_title'))).toBeVisible();
    await page.getByText('Free', { exact: true }).click();
    await page.getByRole('button', { name: t('onboarding.next') }).click();

    await expect(page.getByText(t('onboarding.step_3_title'))).toBeVisible();
    await page.getByText('GymBro', { exact: true }).click();
    await page.getByRole('button', { name: t('onboarding.next') }).click();

    await expect(page.getByText(t('onboarding.integrations_title'))).toBeVisible();
    await page.getByRole('button', { name: t('onboarding.finish') }).click();

    await expect(page.getByText(t('onboarding.success_title'))).toBeVisible();
    await page.getByRole('button', { name: t('onboarding.go_to_dashboard') }).click();

    await expect(page).toHaveURL(/.*dashboard/, { timeout: 15000 });
    const visibleNav = page.locator('[data-testid="mobile-nav"]:visible, [data-testid="desktop-nav"]:visible').first();
    await expect(visibleNav).toBeVisible({ timeout: 15000 });
    await expect(page.getByTestId('dashboard-bento')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText(/Bom dia|Good morning/i)).toBeVisible({ timeout: 15000 });
  });
});
