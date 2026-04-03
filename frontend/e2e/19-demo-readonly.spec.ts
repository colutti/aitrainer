import { test, expect } from './fixtures';
import { loginDemoUserViaUi } from './helpers/bootstrap';

test.describe('Demo Read-Only', () => {
  test('can view the full app but cannot mutate data', async ({ page }) => {
    await loginDemoUserViaUi(page);

    await expect(page).toHaveURL(/\/dashboard(?:\?.*)?$/);
    await expect(page.getByTestId('dashboard-bento')).toBeVisible({ timeout: 15000 });

    await page.goto('/dashboard/chat');
    await expect(page.getByText(/Demo read-only/i).first()).toBeVisible();
    await expect(page.getByTestId('chat-input')).toBeDisabled();

    await page.goto('/dashboard/body');
    const weightTab = page.getByTestId('body-tab-weight');
    const nutritionTab = page.getByTestId('body-tab-nutrition');
    await expect(weightTab).toBeVisible();
    await expect(nutritionTab).toBeVisible();
    await weightTab.click();
    await expect(page.getByRole('button', { name: /Registrar Peso|Register Weight|Registrar Peso/i })).toBeDisabled();
    await nutritionTab.click();
    await expect(page.getByRole('button', { name: /Registrar Refei..o|Register Meal|Registrar Comida/i })).toBeDisabled();

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
  });
});
