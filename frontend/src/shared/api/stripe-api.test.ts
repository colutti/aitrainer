import { beforeEach, describe, expect, it, vi } from 'vitest';

import { httpClient } from './http-client';
import { stripeApi } from './stripe-api';

vi.mock('./http-client', () => ({
  httpClient: vi.fn(),
}));

describe('stripeApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('creates a checkout session and returns the redirect url', async () => {
    vi.mocked(httpClient).mockResolvedValue({
      url: 'https://checkout.stripe.test/session',
    });

    const result = await stripeApi.createCheckoutSession(
      'price_123',
      'https://app.test/success',
      'https://app.test/cancel',
    );

    expect(httpClient).toHaveBeenCalledWith('/stripe/create-checkout-session', {
      method: 'POST',
      body: JSON.stringify({
        price_id: 'price_123',
        success_url: 'https://app.test/success',
        cancel_url: 'https://app.test/cancel',
      }),
    });
    expect(result).toBe('https://checkout.stripe.test/session');
  });

  it('throws when checkout session response is empty', async () => {
    vi.mocked(httpClient).mockResolvedValue(undefined);

    await expect(
      stripeApi.createCheckoutSession(
        'price_123',
        'https://app.test/success',
        'https://app.test/cancel',
      )
    ).rejects.toThrow('Failed to create checkout session');
  });

  it('creates a portal session and returns the redirect url', async () => {
    vi.mocked(httpClient).mockResolvedValue({
      url: 'https://billing.stripe.test/portal',
    });

    const result = await stripeApi.createPortalSession('https://app.test/return');

    expect(httpClient).toHaveBeenCalledWith('/stripe/create-portal-session', {
      method: 'POST',
      body: JSON.stringify({
        return_url: 'https://app.test/return',
      }),
    });
    expect(result).toBe('https://billing.stripe.test/portal');
  });

  it('throws when portal session response is empty', async () => {
    vi.mocked(httpClient).mockResolvedValue(undefined);

    await expect(
      stripeApi.createPortalSession('https://app.test/return')
    ).rejects.toThrow('Failed to create portal session');
  });
});
