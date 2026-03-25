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
    expect(screen.getByText(/Pronto para evoluir/i)).toBeInTheDocument();
  });

  it('should navigate to login when button clicked', () => {
    render(<FinalCTA />);
    const btn = screen.getByRole('button', { name: /Criar minha conta/i });
    fireEvent.click(btn);
    expect(mockNavigate).toHaveBeenCalledWith('/login?mode=register');
  });
});
