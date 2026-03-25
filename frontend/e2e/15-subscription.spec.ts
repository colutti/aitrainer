import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Subscription Feature', () => {
  test('should verify subscription page and plans', async ({ authenticatedPage, ui }) => {
    // 1. Navigate to Settings
    await ui.navigateTo('settings');
    
    // 2. Click Subscription Tab
    const subscriptionTab = authenticatedPage.getByRole('link', { name: t('settings.tabs.subscription') });
    await subscriptionTab.click();
    await expect(authenticatedPage).toHaveURL(/.*settings\/subscription/);

    // 3. Verify Active Plan Section
    const activePlanTitle = authenticatedPage.getByText(t('settings.subscription.active')).first();
    await expect(activePlanTitle).toBeVisible();

    // The user created in tests is Free by default
    const currentPlan = authenticatedPage.locator('h3', { hasText: /Free|Premium|Basic|Pro/i }).first();
    await expect(currentPlan).toBeVisible();

    // 4. Verify Available Plans
    const upgradeButton = authenticatedPage.getByText(t('settings.subscription.upgrade')).first();
    await expect(upgradeButton).toBeVisible();
  });

  test('should show payment success toast via query param', async ({ authenticatedPage, ui }) => {
    // Navigate to dashboard with payment=success
    await authenticatedPage.goto('/dashboard?payment=success');
    
    // Wait for the success toast
    await ui.waitForToast('landing.subscription.payment_success_message');
  });
});
