import { describe, it, expect, vi } from 'vitest';

import { render, screen, fireEvent } from '../../../shared/utils/test-utils';

import { StickyMobileCTA } from './StickyMobileCTA';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('StickyMobileCTA Component', () => {
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
