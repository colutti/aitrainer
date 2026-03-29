import { describe, it, expect, vi, beforeEach } from 'vitest';

import esES from '../../../locales/es-ES.json';
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
    expect(screen.getByRole('button', { name: /assinar premium/i })).toBeInTheDocument();
  });

  it('keeps the spanish pricing locale contract complete', () => {
    expect(esES.landing.plans.items.free.description).toBeTruthy();
    expect(esES.landing.plans.items.free.button).toBeTruthy();
    expect(esES.landing.plans.items.basic.description).toBeTruthy();
    expect(esES.landing.plans.items.basic.button).toBeTruthy();
    expect(esES.landing.plans.items.pro.description).toBeTruthy();
    expect(esES.landing.plans.items.pro.button).toBeTruthy();
    expect(esES.landing.plans.items.premium.description).toBeTruthy();
    expect(esES.landing.plans.items.premium.button).toBeTruthy();
  });

  it('should navigate to login with pro plan if not authenticated', () => {
    render(<Pricing />);
    
    const proBtn = screen.getByTestId('plan-button-pro');
    fireEvent.click(proBtn);
    expect(mockNavigate).toHaveBeenCalledWith('/login?mode=register&plan=pro');
  });
});
