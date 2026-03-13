import { httpClient } from './http-client';

export interface CheckoutSessionResponse {
  url: string;
}

export const stripeApi = {
  createCheckoutSession: async (priceId: string, successUrl: string, cancelUrl: string): Promise<string> => {
    const response = await httpClient<CheckoutSessionResponse>('/stripe/create-checkout-session', {
      method: 'POST',
      body: JSON.stringify({
        price_id: priceId,
        success_url: successUrl,
        cancel_url: cancelUrl,
      }),
    });
    
    if (!response) {
      throw new Error('Failed to create checkout session');
    }
    
    return response.url;
  },

  createPortalSession: async (returnUrl: string): Promise<string> => {
    const response = await httpClient<CheckoutSessionResponse>('/stripe/create-portal-session', {
      method: 'POST',
      body: JSON.stringify({
        return_url: returnUrl,
      }),
    });
    
    if (!response) {
      throw new Error('Failed to create portal session');
    }
    
    return response.url;
  },
};
