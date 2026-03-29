import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Settings journey', () => {
  test('navigates across all settings tabs and renders each route', async ({ authenticatedPage, ui }) => {
    await authenticatedPage.goto('/dashboard/settings', { waitUntil: 'networkidle' });
    await expect(authenticatedPage.getByText(t('settings.title'))).toBeVisible({ timeout: 15000 });

    await authenticatedPage.getByRole('link', { name: t('settings.tabs.profile') }).click();
    await expect(authenticatedPage.getByTestId('profile-form')).toBeVisible({ timeout: 15000 });

    await authenticatedPage.getByRole('link', { name: t('settings.tabs.subscription', 'Assinatura') }).click();
    await expect(authenticatedPage.getByText(t('settings.subscription.title'))).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByTestId('subscription-plan-btn-basic')).toBeVisible({ timeout: 15000 });

    await authenticatedPage.getByRole('link', { name: t('settings.tabs.memories') }).click();
    await expect(authenticatedPage.getByText(t('memories.title'))).toBeVisible({ timeout: 15000 });

    await authenticatedPage.getByRole('link', { name: t('settings.tabs.trainer') }).click();
    await expect(authenticatedPage.getByTestId('trainer-card-gymbro')).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByTestId('trainer-card-atlas').getByTestId('lock-icon')).toBeVisible({
      timeout: 15000,
    });

    await authenticatedPage.getByRole('link', { name: t('settings.tabs.integrations') }).click();
    await expect(authenticatedPage.getByText(t('settings.integrations.hevy.title'))).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByText(t('settings.integrations.telegram.title'))).toBeVisible({
      timeout: 15000,
    });
    await expect(authenticatedPage.getByText(t('settings.integrations.imports.title'))).toBeVisible({
      timeout: 15000,
    });

    await ui.navigateTo('dashboard');
    await expect(authenticatedPage.getByTestId('dashboard-bento')).toBeVisible({ timeout: 15000 });
  });
});
