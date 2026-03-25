import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Integrations Feature', () => {
  test('should load integrations page and display connection options', async ({ authenticatedPage, ui }) => {
    // 1. Navigate to Settings
    await ui.navigateTo('settings');
    
    // 2. Click Integrations Tab
    const integrationsTab = authenticatedPage.getByRole('link', { name: t('settings.tabs.integrations') });
    await integrationsTab.click();
    await expect(authenticatedPage).toHaveURL(/.*settings\/integrations/);

    // 3. Verify Hevy Integration Section
    const hevyTitle = authenticatedPage.getByRole('heading', { name: 'Hevy' }).first();
    await expect(hevyTitle).toBeVisible();

    // Check if a key is already active, if so, remove it to test the empty state
    const removeHevyBtn = authenticatedPage.getByRole('button', { name: t('settings.integrations.shared.remove') });
    if (await removeHevyBtn.isVisible()) {
      await removeHevyBtn.click();
      await authenticatedPage.waitForTimeout(1000);
    }

    const hevyInput = authenticatedPage.getByPlaceholder(t('settings.integrations.hevy.hevy_placeholder') || 'API Key');
    await expect(hevyInput).toBeVisible({ timeout: 10000 });
    
    // Check if the connect button is present
    const confirmBtn = authenticatedPage.getByRole('button', { name: t('common.confirm') }).first();
    await expect(confirmBtn).toBeVisible();

    // 4. Verify Telegram Integration Section
    const telegramTitle = authenticatedPage.getByRole('heading', { name: 'Telegram' }).first();
    await expect(telegramTitle).toBeVisible();

    // 5. Verify CSV Import Section
    const importTitle = authenticatedPage.getByRole('heading', { name: t('settings.integrations.imports.title') });
    await expect(importTitle).toBeVisible();
  });
});
