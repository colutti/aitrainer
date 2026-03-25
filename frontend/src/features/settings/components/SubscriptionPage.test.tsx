import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useAuthStore } from '../../../shared/hooks/useAuth';

import SubscriptionPage from './SubscriptionPage';

// Mock the auth store
vi.mock('../../../shared/hooks/useAuth', () => ({
  useAuthStore: vi.fn(),
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
      userInfo: { subscription_plan: 'Premium', has_stripe_customer: true },
      loadUserInfo: mockLoadUserInfo,
    });
  });

  it('should call loadUserInfo on mount to refresh subscription status', async () => {
    render(<SubscriptionPage />);
    await waitFor(() => {
      expect(mockLoadUserInfo).toHaveBeenCalledTimes(1);
    });
  });

  it('should show "Premium" as active plan after loading', async () => {
    render(<SubscriptionPage />);

    // Wait for loading to finish
    await waitFor(() => {
      expect(screen.queryByText('common.loading')).not.toBeInTheDocument();
    });

    // The "Plano Atual" text is rendered when isCurrent is true (both in badge and button)
    const elements = screen.getAllByText('Plano Atual');
    expect(elements.length).toBeGreaterThan(0);
  });
});
