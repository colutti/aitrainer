import { STRIPE_PRICE_IDS } from '../src/shared/constants/stripe';

import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Subscription Feature', () => {
  test('loads plans and sends a checkout request when upgrading', async ({ authenticatedPage, ui }) => {
    const checkoutRequests: Record<string, unknown>[] = [];

    await authenticatedPage.route('**/stripe/create-checkout-session', async route => {
      checkoutRequests.push(route.request().postDataJSON() as Record<string, unknown>);
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ url: 'https://checkout.stripe.com/c/pay/test-checkout' }),
      });
    });

    await ui.navigateTo('settings');
    await authenticatedPage.getByRole('link', { name: t('settings.tabs.subscription') }).click();
    await authenticatedPage.waitForLoadState('networkidle');

    await expect(authenticatedPage.getByText(t('settings.subscription.title')).first()).toBeVisible({
      timeout: 15000,
    });
    await expect(authenticatedPage.getByTestId('subscription-plan-btn-basic')).toBeVisible();

    await authenticatedPage.getByTestId('subscription-plan-btn-basic').click();
    await expect(authenticatedPage).toHaveURL(/checkout\.stripe\.com\/c\/pay\/test-checkout/);

    expect(checkoutRequests).toHaveLength(1);
    expect(checkoutRequests[0]?.price_id).toBe(STRIPE_PRICE_IDS.basic);
    expect(String(checkoutRequests[0]?.success_url)).toContain('/dashboard?payment=success');
    expect(String(checkoutRequests[0]?.cancel_url)).toContain('/dashboard/settings/subscription?payment=cancel');
  });

  test('shows payment success toast via query param', async ({ authenticatedPage, ui }) => {
    await authenticatedPage.goto('/dashboard?payment=success');
    await ui.waitForToast('landing.subscription.payment_success_message');
  });
});
