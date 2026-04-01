import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { SubscriptionView } from './SubscriptionView';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: 'pt-BR' }
  }),
}));

const mockPlans = [
  { id: 'free', name: 'Free', price: '0', icon: vi.fn() as any, features: ['F1'] },
  { id: 'basic', name: 'Basic', price: '24', icon: vi.fn() as any, features: ['F1', 'F2'] },
  { id: 'pro', name: 'Pro', price: '49', icon: vi.fn() as any, features: ['F1', 'F2'] },
  { id: 'premium', name: 'Premium', price: '99', icon: vi.fn() as any, features: ['F1', 'F2'] },
];

const mockProps = {
  currentPlan: 'free',
  plans: mockPlans,
  loading: null,
  isInitialLoading: false,
  isPt: true,
  hasStripeCustomer: false,
  isReadOnly: false,
  onSubscribe: vi.fn(),
  onManage: vi.fn(),
};

describe('SubscriptionView', () => {
  it('renders all plans correctly', () => {
    render(<SubscriptionView {...mockProps} />);
    expect(screen.getByText('Free')).toBeInTheDocument();
    expect(screen.getByText('Basic')).toBeInTheDocument();
    expect(screen.getByText('Pro')).toBeInTheDocument();
    expect(screen.getByText('Premium')).toBeInTheDocument();
  });

  it('marks current plan correctly', () => {
    render(<SubscriptionView {...mockProps} currentPlan="pro" />);
    // Check for "active" label (appears in badge and button)
    expect(screen.getAllByText('settings.subscription.active').length).toBeGreaterThan(0);
  });

  it('calls onSubscribe when a plan button is clicked', () => {
    render(<SubscriptionView {...mockProps} />);
    const proBtn = screen.getByTestId('subscription-plan-btn-pro');
    fireEvent.click(proBtn);
    expect(mockProps.onSubscribe).toHaveBeenCalledWith('pro');
  });

  it('calls onManage when manage button is clicked', () => {
    render(<SubscriptionView {...mockProps} currentPlan="pro" hasStripeCustomer={true} />);
    const manageBtn = screen.getByText('settings.subscription.manage_button');
    fireEvent.click(manageBtn);
    expect(mockProps.onManage).toHaveBeenCalled();
  });

  it('disables plan actions in read-only mode', () => {
    render(<SubscriptionView {...mockProps} isReadOnly />);
    expect(screen.getByTestId('subscription-plan-btn-pro')).toBeDisabled();
    expect(screen.getByText('Demo Read-Only')).toBeInTheDocument();
  });

  it('shows downgrade for lower plans and upgrade for higher plans based on current plan hierarchy', () => {
    render(<SubscriptionView {...mockProps} currentPlan="pro" hasStripeCustomer={false} />);
    expect(screen.getByTestId('subscription-plan-btn-basic')).toHaveTextContent('settings.subscription.downgrade');
    expect(screen.getByTestId('subscription-plan-btn-premium')).toHaveTextContent('settings.subscription.upgrade');
  });
});
