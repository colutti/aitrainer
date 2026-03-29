import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Integrations Feature', () => {
  test('keeps Hevy connected after reload and generates a Telegram code', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/settings/integrations');
    await authenticatedPage.waitForLoadState('networkidle');

    await expect(authenticatedPage.getByText(/Ativo: \*\*\*\*\d{4}|Active \*\*\*\*\d{4}/i)).toBeVisible({
      timeout: 15000,
    });
    await expect(authenticatedPage.getByRole('button', { name: t('settings.integrations.hevy.sync_button') })).toBeVisible();

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await authenticatedPage.goto('/dashboard/settings/integrations');
    await authenticatedPage.waitForLoadState('networkidle');
    await expect(authenticatedPage.getByText(/Ativo: \*\*\*\*\d{4}|Active \*\*\*\*\d{4}/i)).toBeVisible({
      timeout: 15000,
    });

    await authenticatedPage.getByRole('button', { name: t('settings.integrations.telegram.generate_code') }).click();
    await expect(authenticatedPage.getByText(/^[A-Z0-9]{6}$/)).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByText(/Abrir Bot|Open Bot|Abrir bot/i)).toBeVisible();
  });
});
