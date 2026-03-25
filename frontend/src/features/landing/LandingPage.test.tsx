import { describe, it, expect, vi, beforeEach } from 'vitest';

import { useAuthStore } from '../../shared/hooks/useAuth';
import { render, screen } from '../../shared/utils/test-utils';

import LandingPage from './LandingPage';

// Mocks
vi.mock('../../shared/hooks/useAuth');
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock child components to speed up and isolate LandingPage
vi.mock('./components/Hero', () => ({ Hero: () => <div data-testid="hero" /> }));
vi.mock('./components/Navbar', () => ({ Navbar: () => <div data-testid="navbar" /> }));
vi.mock('./components/Footer', () => ({ Footer: () => <div data-testid="footer" /> }));

describe('LandingPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuthStore).mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
    } as any);
  });

  it('should render landing page components', () => {
    render(<LandingPage />);
    
    expect(screen.getByTestId('navbar')).toBeInTheDocument();
    expect(screen.getByTestId('hero')).toBeInTheDocument();
    expect(screen.getByTestId('footer')).toBeInTheDocument();
  });

  it('should redirect to dashboard if authenticated', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
    } as any);

    render(<LandingPage />);
    
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true });
  });
});
