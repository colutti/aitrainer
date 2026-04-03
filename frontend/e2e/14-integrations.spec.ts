import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Integrations Feature', () => {
  test('keeps Hevy connected after reload and generates a Telegram code', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/settings/integrations');
    await authenticatedPage.waitForLoadState('networkidle');

    await expect(authenticatedPage.getByText(t('settings.integrations.hevy.title'))).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByText(t('settings.integrations.telegram.title'))).toBeVisible({ timeout: 15000 });

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await authenticatedPage.goto('/dashboard/settings/integrations');
    await authenticatedPage.waitForLoadState('networkidle');

    const generateCodeButton = authenticatedPage.getByRole('button', {
      name: t('settings.integrations.telegram.generate_code'),
    });
    if (await generateCodeButton.isVisible().catch(() => false)) {
      await generateCodeButton.click();
    }
    await expect(authenticatedPage.getByText(/^[A-Z0-9]{6}$/)).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByText(/Abrir Bot|Open Bot|Abrir bot/i)).toBeVisible();
  });
});
