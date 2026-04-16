import { describe, it, expect, vi } from 'vitest';

import { render, screen, fireEvent } from '../../../shared/utils/test-utils';

import { Hero } from './Hero';

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

describe('Hero Component', () => {
  it('should disable signup CTA when signups are off', () => {
    mockUsePublicConfig.mockReturnValueOnce({
      enableNewUserSignups: false,
      isLoading: false,
      hasLoaded: true,
    });
    render(<Hero />);

    expect(screen.getByRole('button', { name: /Começar teste grátis/i })).toBeDisabled();
  });

  it('should render hero content', () => {
    render(<Hero />);

    expect(screen.getByText(/Transforme sua rotina em evolu[cç][aã]o consistente/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Ver demo/i })).toBeInTheDocument();
  });

  it('should navigate to register when CTA clicked', () => {
    render(<Hero />);

    const ctaBtn = screen.getByText(/Começar teste grátis/i);
    fireEvent.click(ctaBtn);
    expect(mockNavigate).toHaveBeenCalledWith('/login?mode=register');
  });
});
