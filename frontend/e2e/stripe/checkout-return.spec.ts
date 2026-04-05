import { test, expect } from '../fixtures';
import { t } from '../helpers/translations';

import { isStripeCheckoutUrl, stripeLiveEnabled } from './fixtures/stripeTestHarness';

test.describe('Stripe Live Checkout Return', () => {
  test('opens Stripe checkout for Pro and returns success to dashboard', async ({ authenticatedPage, ui }) => {
    test.skip(!stripeLiveEnabled, 'Stripe live mode disabled');

    await ui.navigateTo('settings');
    await authenticatedPage.getByRole('link', { name: t('settings.tabs.subscription') }).click();
    await authenticatedPage.waitForLoadState('networkidle');

    await expect(authenticatedPage.getByTestId('subscription-plan-btn-pro')).toBeVisible({ timeout: 15000 });
    await authenticatedPage.getByTestId('subscription-plan-btn-pro').click();

    await authenticatedPage.waitForURL(url => isStripeCheckoutUrl(url.toString()), { timeout: 20000 });
  });
});
