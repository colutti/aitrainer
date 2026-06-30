import { STRIPE_PRICE_IDS } from '../src/shared/constants/stripe';

import { test, expect } from './fixtures';
import { bootstrapOnboardedUser } from './helpers/bootstrap';
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

  test('opens the billing portal for a paid subscriber', async ({ page, ui }, testInfo) => {
    await page.route('**/user/me', async route => {
      const response = await route.fetch();
      const body = await response.json() as Record<string, unknown>;
      await route.fulfill({
        response,
        body: JSON.stringify({
          ...body,
          subscription_plan: 'Pro',
          has_stripe_customer: true,
        }),
      });
    });

    const portalRequests: Record<string, unknown>[] = [];

    await page.route('**/stripe/create-portal-session', async route => {
      portalRequests.push(route.request().postDataJSON() as Record<string, unknown>);
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ url: 'https://billing.stripe.com/p/session-test' }),
      });
    });

    const authenticatedPage = await bootstrapOnboardedUser(page, testInfo, {
      subscriptionPlan: 'Pro',
    });

    await ui.navigateTo('settings');
    await authenticatedPage.getByRole('link', { name: t('settings.tabs.subscription') }).click();
    await authenticatedPage.waitForLoadState('networkidle');

    await expect(authenticatedPage.getByTestId('btn-manage-subscription')).toBeVisible({ timeout: 15000 });

    await authenticatedPage.getByTestId('btn-manage-subscription').click();
    await expect(authenticatedPage).toHaveURL(/billing\.stripe\.com\/p\/session-test/);

    expect(portalRequests).toHaveLength(1);
    expect(String(portalRequests[0]?.return_url)).toContain('/dashboard/settings/subscription');
  });

  test('shows payment success toast via query param', async ({ authenticatedPage, ui }) => {
    await authenticatedPage.goto('/dashboard?payment=success');
    await ui.waitForToast('landing.subscription.payment_success_message');
  });
});
