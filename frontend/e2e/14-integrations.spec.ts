import { test, expect } from './fixtures';
import { gotoAppRoute } from './helpers/bootstrap';
import { bootstrapOnboardedUser } from './helpers/bootstrap';

const apiBaseURL = process.env.E2E_API_BASE_URL ?? 'http://localhost:8000';

test.describe('Integrations Feature', () => {
  test('saves and removes a Hevy key for a pro user with persistence across reload', async ({ page }, testInfo) => {
    const authenticatedPage = await bootstrapOnboardedUser(page, testInfo, {
      subscriptionPlan: 'Pro',
    });

    await gotoAppRoute(authenticatedPage, '/dashboard/settings/integrations');

    const hevyKey = 'hevy_test_key_4321';
    await authenticatedPage.getByPlaceholder(/API Key|Chave API|Clave API/i).fill(hevyKey);
    await authenticatedPage.getByRole('button', { name: /Confirm|Confirmar/i }).click();
    await expect(authenticatedPage.getByText('****4321')).toBeVisible({ timeout: 15000 });

    await authenticatedPage.reload({ waitUntil: 'commit' });
    await gotoAppRoute(authenticatedPage, '/dashboard/settings/integrations');
    await expect(authenticatedPage.getByText('****4321')).toBeVisible({ timeout: 15000 });

    await authenticatedPage.getByRole('button', { name: /Remove|Remover/i }).click();
    await expect(authenticatedPage.getByPlaceholder(/API Key|Chave API|Clave API/i)).toBeVisible({
      timeout: 15000,
    });

    await authenticatedPage.reload({ waitUntil: 'commit' });
    await gotoAppRoute(authenticatedPage, '/dashboard/settings/integrations');
    await expect(authenticatedPage.getByPlaceholder(/API Key|Chave API|Clave API/i)).toBeVisible({
      timeout: 15000,
    });
  });

  test('keeps integrations page stable after reload and generates a Telegram code for a pro user', async ({ page }, testInfo) => {
    const authenticatedPage = await bootstrapOnboardedUser(page, testInfo, {
      subscriptionPlan: 'Pro',
    });

    await gotoAppRoute(authenticatedPage, '/dashboard/settings/integrations');

    await expect(authenticatedPage.getByText(/Hevy/i)).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByText(/Telegram Bot/i)).toBeVisible({ timeout: 15000 });

    await authenticatedPage.reload({ waitUntil: 'commit' });
    await gotoAppRoute(authenticatedPage, '/dashboard/settings/integrations');

    const generateCodeButton = authenticatedPage.getByRole('button', {
      name: /Generate Code|Gerar Código|Generar Código/i,
    });
    if (await generateCodeButton.isVisible().catch(() => false)) {
      await generateCodeButton.click();
    }
    await expect(authenticatedPage.getByText(/^[A-Z0-9]{6}$/)).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByText(/Abrir Bot|Open Bot|Abrir bot/i)).toBeVisible();
  });

  test('links Telegram, toggles workout notifications, and keeps the preference after reload', async ({ page }, testInfo) => {
    const authenticatedPage = await bootstrapOnboardedUser(page, testInfo, {
      subscriptionPlan: 'Pro',
    });

    const token = await authenticatedPage.evaluate(() => localStorage.getItem('auth_token') ?? '');

    const seedLinkResponse = await authenticatedPage.request.post(`${apiBaseURL}/telegram/e2e-link`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      data: {
        chat_id: 987654321,
        username: 'e2e_telegram_user',
      },
    });
    expect(seedLinkResponse.ok()).toBeTruthy();

    await gotoAppRoute(authenticatedPage, '/dashboard/settings/integrations');

    await expect(authenticatedPage.getByText(/e2e_telegram_user/i)).toBeVisible({ timeout: 15000 });

    const workoutNotifyCheckbox = authenticatedPage.locator('input[type="checkbox"]').first();
    await expect(workoutNotifyCheckbox).toBeChecked();

    await workoutNotifyCheckbox.click();
    await expect(workoutNotifyCheckbox).not.toBeChecked();

    await authenticatedPage.reload({ waitUntil: 'commit' });
    await gotoAppRoute(authenticatedPage, '/dashboard/settings/integrations');

    await expect(authenticatedPage.getByText(/e2e_telegram_user/i)).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.locator('input[type="checkbox"]').first()).not.toBeChecked();
  });
});
