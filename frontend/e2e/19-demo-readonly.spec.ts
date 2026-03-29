import { test, expect } from './fixtures';
import { loginDemoUserViaUi } from './helpers/bootstrap';
import { t } from './helpers/translations';

test.describe('Demo Read-Only', () => {
  test('can view the full app but cannot mutate data', async ({ page }) => {
    await loginDemoUserViaUi(page);

    await expect(page).toHaveURL(/\/dashboard(?:\?.*)?$/);
    await expect(page.getByTestId('dashboard-bento')).toBeVisible({ timeout: 15000 });

    await page.goto('/dashboard/chat');
    await expect(page.locator('div.bg-amber-500\\/10').filter({ hasText: 'Demo read-only' }).first()).toBeVisible();
    await expect(page.getByPlaceholder(t('chat.input_placeholder'))).toBeDisabled();

    await page.goto('/dashboard/body');
    const weightTab = t('body.weight_title');
    const nutritionTab = t('body.nutrition_title');
    await expect(page.getByRole('button', { name: weightTab }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: nutritionTab }).first()).toBeVisible();
    await page.getByRole('button', { name: weightTab }).first().click();
    await expect(page.getByTestId('weight-log-card').first()).toBeVisible();
    await page.getByTestId('weight-log-card').first().click();
    await expect(page.getByText('Demo Read-Only', { exact: true }).first()).toBeVisible();
    await expect(page.getByTestId('weight-kg')).toBeDisabled();

    await page.goto('/dashboard/settings/profile');
    await expect(page.getByText('Demo Read-Only', { exact: true }).first()).toBeVisible();
    await expect(page.getByTestId('profile-form')).toBeVisible();
    await expect(page.getByTestId('profile-name')).toBeDisabled();

    await page.goto('/dashboard/settings/subscription');
    await expect(page.getByText('Demo Read-Only', { exact: true }).first()).toBeVisible();

    await page.goto('/dashboard/settings/integrations');
    await expect(page.getByText('Demo Read-Only', { exact: true }).first()).toBeVisible();

    await page.goto('/dashboard/settings/memories');
    await expect(page.getByText('Demo Read-Only', { exact: true }).first()).toBeVisible();
    await expect(page.getByTestId('memory-card').first()).toBeVisible();
  });
});
