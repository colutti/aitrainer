import { describe, it, expect, vi } from 'vitest';

import { render, screen, fireEvent } from '../../../shared/utils/test-utils';

import { FinalCTA } from './FinalCTA';

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

describe('FinalCTA Component', () => {
  it('should disable CTA when signups are off', () => {
    mockUsePublicConfig.mockReturnValueOnce({
      enableNewUserSignups: false,
      isLoading: false,
      hasLoaded: true,
    });
    render(<FinalCTA />);

    expect(screen.getByRole('button', { name: /Começar teste grátis/i })).toBeDisabled();
  });

  it('should render final call to action', () => {
    render(<FinalCTA />);
    expect(screen.getByText(/Comece a construir uma rotina mais inteligente/i)).toBeInTheDocument();
  });

  it('should navigate to login when button clicked', () => {
    render(<FinalCTA />);
    const btn = screen.getByRole('button', { name: /Começar teste grátis/i });
    fireEvent.click(btn);
    expect(mockNavigate).toHaveBeenCalledWith('/login?mode=register');
  });
});
