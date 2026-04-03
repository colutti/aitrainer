import { waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import enUS from '../../../locales/en-US.json';
import esES from '../../../locales/es-ES.json';
import ptBR from '../../../locales/pt-BR.json';
import { stripeApi } from '../../../shared/api/stripe-api';
import { useAuthStore } from '../../../shared/hooks/useAuth';
import { render, screen, fireEvent } from '../../../shared/utils/test-utils';

import { Pricing } from './Pricing';

// Mocks
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('../../../shared/hooks/useAuth');
vi.mock('../../../shared/api/stripe-api', () => ({
  stripeApi: {
    createCheckoutSession: vi.fn(),
  },
}));
vi.mock('../../../shared/hooks/useNotification', () => ({
  useNotificationStore: () => ({
    success: vi.fn(),
    error: vi.fn(),
  }),
}));

describe('Pricing Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuthStore).mockReturnValue({
      isAuthenticated: false,
    } as any);
  });

  it('should render pricing plans', () => {
    render(<Pricing />);
    
    expect(screen.getByText(/Escolha o nível da sua performance/i)).toBeInTheDocument();
    expect(screen.getByText('Free')).toBeInTheDocument();
    expect(screen.getByText('Pro')).toBeInTheDocument();
    expect(screen.queryByText('Premium')).not.toBeInTheDocument();
  });

  it('should navigate to register with free plan when clicked', () => {
    render(<Pricing />);
    
    const freeBtn = screen.getByTestId('plan-button-free');
    fireEvent.click(freeBtn);
    expect(mockNavigate).toHaveBeenCalledWith('/login?mode=register&plan=free');
  });

  it('renders a translated CTA for each pricing plan', () => {
    render(<Pricing />);

    expect(screen.getByRole('button', { name: /come[cç]ar gr[aá]tis/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /assinar basic/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /assinar pro/i })).toBeInTheDocument();
  });

  it('keeps the spanish pricing locale contract complete', () => {
    expect(esES.landing.plans.items.free.description).toBeTruthy();
    expect(esES.landing.plans.items.free.button).toBeTruthy();
    expect(esES.landing.plans.items.basic.description).toBeTruthy();
    expect(esES.landing.plans.items.basic.button).toBeTruthy();
    expect(esES.landing.plans.items.pro.description).toBeTruthy();
    expect(esES.landing.plans.items.pro.button).toBeTruthy();
    expect(esES.landing.plans.recommended).toBeTruthy();
  });

  it('keeps pro copy aligned with photo analysis for all locales', () => {
    expect(ptBR.landing.plans.items.pro.description).toMatch(/fotos/i);
    expect(ptBR.landing.plans.items.pro.description).toMatch(/automa/i);
    expect(enUS.landing.plans.items.pro.description).toMatch(/photo/i);
    expect(enUS.landing.plans.items.pro.description).toMatch(/automation/i);
    expect(esES.landing.plans.items.pro.description).toMatch(/fotos/i);
    expect(esES.landing.plans.items.pro.description).toMatch(/automatiza/i);

    expect(ptBR.landing.plans.items.pro.features.join(' ')).toMatch(/Telegram/i);
    expect(enUS.landing.plans.items.pro.features.join(' ')).toMatch(/Telegram/i);
    expect(esES.landing.plans.items.pro.features.join(' ')).toMatch(/Telegram/i);
  });

  it('should navigate to login with pro plan if not authenticated', () => {
    render(<Pricing />);
    
    const proBtn = screen.getByTestId('plan-button-pro');
    fireEvent.click(proBtn);
    expect(mockNavigate).toHaveBeenCalledWith('/login?mode=register&plan=pro');
  });

  it('creates checkout session for authenticated pro users', async () => {
    vi.mocked(useAuthStore).mockReturnValue({ isAuthenticated: true } as any);
    vi.mocked(stripeApi.createCheckoutSession).mockRejectedValue(new Error('stripe down'));

    render(<Pricing />);

    fireEvent.click(screen.getByTestId('plan-button-pro'));

    await waitFor(() => {
      expect(stripeApi.createCheckoutSession).toHaveBeenCalledWith(
        'price_1TAPTBPTisrIM5tNKY7Nxw3i',
        `${window.location.origin}/dashboard?payment=success`,
        `${window.location.origin}/#planos`
      );
    });
  });
});
