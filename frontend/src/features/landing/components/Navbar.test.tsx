import { describe, it, expect, vi } from 'vitest';

import { render, screen, fireEvent } from '../../../shared/utils/test-utils';

import { Navbar } from './Navbar';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Navbar Component', () => {
  it('should render logo and links', () => {
    render(<Navbar />);
    expect(screen.getByAltText('FityQ')).toBeInTheDocument();
    expect(screen.getByText('FityQ')).toBeInTheDocument();
  });

  it('should navigate to login when button clicked', () => {
    render(<Navbar />);
    const loginBtns = screen.getAllByText(/Login/i);
    fireEvent.click(loginBtns[0]!);
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('should toggle mobile menu', () => {
    // Force mobile viewport
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 375 });
    
    render(<Navbar />);
    const toggleBtn = screen.getByLabelText(/Toggle menu/i);
    
    fireEvent.click(toggleBtn);
    // After toggle, mobile links should be visible
    const mobileLinks = screen.getAllByRole('button');
    expect(mobileLinks.length).toBeGreaterThan(4);
  });
});
