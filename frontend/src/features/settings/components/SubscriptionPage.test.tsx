import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import ptBR from '../../../locales/pt-BR.json';
import { stripeApi } from '../../../shared/api/stripe-api';
import { useAuthStore } from '../../../shared/hooks/useAuth';
import { useDemoMode } from '../../../shared/hooks/useDemoMode';

import SubscriptionPage from './SubscriptionPage';

// Mock the auth store
vi.mock('../../../shared/hooks/useAuth', () => ({
  useAuthStore: vi.fn(),
}));
vi.mock('../../../shared/hooks/useDemoMode', () => ({
  useDemoMode: vi.fn(),
}));

// Mock the notification store
vi.mock('../../../shared/hooks/useNotification', () => ({
  useNotificationStore: vi.fn(() => ({
    error: vi.fn(),
    success: vi.fn(),
  })),
}));

// Mock the stripe API
vi.mock('../../../shared/api/stripe-api', () => ({
  stripeApi: {
    createCheckoutSession: vi.fn(),
    createPortalSession: vi.fn(),
  },
}));

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, options?: any) => {
      if (key.includes('features')) return ['Feature 1', 'Feature 2'];
      if (key === 'settings.subscription.active') return options?.defaultValue || 'Plano Atual';
      return key;
    },
    i18n: { language: 'en' },
  }),
}));

describe('SubscriptionPage', () => {
  const mockLoadUserInfo = vi.fn().mockResolvedValue(undefined);

  beforeEach(() => {
    vi.clearAllMocks();
    (useAuthStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      userInfo: { subscription_plan: 'Pro', has_stripe_customer: true },
      loadUserInfo: mockLoadUserInfo,
    });
    (useDemoMode as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      isReadOnly: false,
    });
  });

  it('should call loadUserInfo on mount to refresh subscription status', async () => {
    render(<SubscriptionPage />);
    await waitFor(() => {
      expect(mockLoadUserInfo).toHaveBeenCalledTimes(1);
    });
  });

  it('should show active plan after loading', async () => {
    render(<SubscriptionPage />);

    // Wait for loading to finish
    await waitFor(() => {
      expect(screen.queryByText('common.loading')).not.toBeInTheDocument();
    });

    // The "Plano Atual" text is rendered when isCurrent is true (both in badge and button)
    const elements = screen.getAllByText('Plano Atual');
    expect(elements.length).toBeGreaterThan(0);
  });

  it('keeps subscription features synced with landing copy for pro and basic', () => {
    expect(ptBR.landing.plans.items.pro.features.join(' ')).toMatch(/Telegram/i);
    expect(ptBR.landing.plans.items.basic.features.join(' ')).toMatch(/100/i);
  });

  it('opens stripe checkout for selected paid plan', async () => {
    (useAuthStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      userInfo: { subscription_plan: 'Free', has_stripe_customer: false },
      loadUserInfo: mockLoadUserInfo,
    });
    vi.mocked(stripeApi.createCheckoutSession).mockRejectedValue(new Error('stripe down'));

    render(<SubscriptionPage />);
    await waitFor(() => {
      expect(screen.queryByText('common.loading')).not.toBeInTheDocument();
    });

    screen.getByTestId('subscription-plan-btn-basic').click();

    await waitFor(() => {
      expect(stripeApi.createCheckoutSession).toHaveBeenCalledWith(
        'price_1TAPTBPTisrIM5tN5Dz3P2en',
        `${window.location.origin}/dashboard?payment=success`,
        `${window.location.origin}/dashboard/settings/subscription?payment=cancel`
      );
    });
  });

  it('opens stripe customer portal for paid user manage action', async () => {
    vi.mocked(stripeApi.createPortalSession).mockRejectedValue(new Error('portal down'));

    render(<SubscriptionPage />);
    await waitFor(() => {
      expect(screen.queryByText('common.loading')).not.toBeInTheDocument();
    });

    screen.getByTestId('btn-manage-subscription').click();

    await waitFor(() => {
      expect(stripeApi.createPortalSession).toHaveBeenCalledWith(
        `${window.location.origin}/dashboard/settings/subscription`
      );
    });
  });
});
