import { describe, it, expect, vi } from 'vitest';

import { render, screen, fireEvent } from '../../../shared/utils/test-utils';

import { FinalCTA } from './FinalCTA';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('FinalCTA Component', () => {
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
