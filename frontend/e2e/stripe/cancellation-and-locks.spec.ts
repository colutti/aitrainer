import crypto from 'node:crypto';

import { test, expect } from '../fixtures';

const webhookSecret = process.env.E2E_STRIPE_TEST_WEBHOOK_SECRET || process.env.STRIPE_WEBHOOK_SECRET || 'whsec_mock';

function stripeSignature(payload: string, secret: string): string {
  const timestamp = Math.floor(Date.now() / 1000);
  const signedPayload = `${timestamp}.${payload}`;
  const signature = crypto.createHmac('sha256', secret).update(signedPayload).digest('hex');
  return `t=${timestamp},v1=${signature}`;
}

test.describe('Stripe Subscription Lock Flow', () => {
  test('downgrades on canceled subscription and locks premium trainer', async ({ authenticatedPage, api }) => {
    const meResponse = await api.get('/user/me');
    expect(meResponse.ok()).toBeTruthy();
    const me = (await meResponse.json()) as { email: string };
    const userEmail = me.email;
    const customerId = `cus_e2e_${Date.now()}`;
    const nowTs = Math.floor(Date.now() / 1000);

    const activeEvent = JSON.stringify({
      id: `evt_active_${Date.now()}`,
      type: 'customer.subscription.updated',
      data: {
        object: {
          id: 'sub_e2e_live',
          customer: customerId,
          status: 'active',
          current_period_start: nowTs,
          metadata: { user_email: userEmail },
          items: { data: [{ price: { id: 'price_1TAPTBPTisrIM5tNKY7Nxw3i' } }] },
        },
      },
    });

    const activeResponse = await api.post('/stripe/webhook', {
      data: activeEvent,
      headers: {
        'Content-Type': 'application/json',
        'stripe-signature': stripeSignature(activeEvent, webhookSecret),
      },
    });
    expect(activeResponse.ok()).toBeTruthy();

    const deletedEvent = JSON.stringify({
      id: `evt_deleted_${Date.now()}`,
      type: 'customer.subscription.deleted',
      data: {
        object: {
          id: 'sub_e2e_live',
          customer: customerId,
        },
      },
    });

    const deletedResponse = await api.post('/stripe/webhook', {
      data: deletedEvent,
      headers: {
        'Content-Type': 'application/json',
        'stripe-signature': stripeSignature(deletedEvent, webhookSecret),
      },
    });
    expect(deletedResponse.ok()).toBeTruthy();

    await authenticatedPage.goto('/dashboard/settings/trainer');
    await authenticatedPage.waitForLoadState('networkidle');
    const atlasCard = authenticatedPage.getByTestId('trainer-card-atlas').first();
    await expect(atlasCard.getByTestId('lock-icon')).toBeVisible();
    await atlasCard.click();
    await expect(authenticatedPage).toHaveURL(/.*settings\/subscription/);
  });
});
