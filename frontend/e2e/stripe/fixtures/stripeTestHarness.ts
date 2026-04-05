export const stripeLiveEnabled = (process.env.E2E_STRIPE_LIVE_TEST_ENABLED ?? '').toLowerCase() === 'true';

export function requireStripeLive(): void {
  if (!stripeLiveEnabled) {
    throw new Error('Stripe live e2e disabled. Set E2E_STRIPE_LIVE_TEST_ENABLED=true');
  }
}

export function isStripeCheckoutUrl(url: string): boolean {
  return url.includes('checkout.stripe.com');
}
