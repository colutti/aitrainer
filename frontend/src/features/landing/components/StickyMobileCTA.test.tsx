import { describe, it, expect, vi } from 'vitest';

import { render, screen, fireEvent } from '../../../shared/utils/test-utils';

import { StickyMobileCTA } from './StickyMobileCTA';

const mockNavigate = vi.fn();
const mockUsePublicConfig = vi.fn(() => ({
  enableNewUserSignups: true,
  isLoading: false,
  hasLoaded: true,
}));

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});
vi.mock('../../../shared/hooks/usePublicConfig', () => ({
  usePublicConfig: () => mockUsePublicConfig(),
}));

describe('StickyMobileCTA Component', () => {
  it('should disable mobile CTA when signups are off', () => {
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 375 });
    Object.defineProperty(window, 'scrollY', { writable: true, configurable: true, value: 600 });
    mockUsePublicConfig.mockReturnValue({
      enableNewUserSignups: false,
      isLoading: false,
      hasLoaded: true,
    });
    
    render(<StickyMobileCTA />);
    fireEvent.scroll(window);

    expect(screen.getByText(/Começar teste grátis/i)).toBeDisabled();
    mockUsePublicConfig.mockReturnValue({
      enableNewUserSignups: true,
      isLoading: false,
      hasLoaded: true,
    });
  });

  it('should render mobile CTA when scrolled and on mobile', () => {
    // Mock window properties
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 375 });
    Object.defineProperty(window, 'scrollY', { writable: true, configurable: true, value: 600 });
    
    render(<StickyMobileCTA />);
    
    // Trigger scroll event manually to update state
    fireEvent.scroll(window);
    
    expect(screen.getByText(/Começar teste grátis/i)).toBeInTheDocument();
  });

  it('should navigate to register when clicked', () => {
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 375 });
    Object.defineProperty(window, 'scrollY', { writable: true, configurable: true, value: 600 });
    
    render(<StickyMobileCTA />);
    fireEvent.scroll(window);
    
    const btn = screen.getByText(/Começar teste grátis/i);
    fireEvent.click(btn);
    expect(mockNavigate).toHaveBeenCalledWith('/login?mode=register');
  });
});
