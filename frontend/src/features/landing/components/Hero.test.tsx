import { describe, it, expect, vi } from 'vitest';

import { render, screen, fireEvent } from '../../../shared/utils/test-utils';

import { Hero } from './Hero';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Hero Component', () => {
  it('should render hero content', () => {
    render(<Hero />);
    
    // We check for some translation keys that should be rendered by our real pt-BR.json in test-utils
    expect(screen.getByText(/Seu Treinador IA Pessoal/i)).toBeInTheDocument();
    expect(screen.getByText(/Inteligência que gera Performance/i)).toBeInTheDocument();
  });

  it('should navigate to register when CTA clicked', () => {
    render(<Hero />);
    
    const ctaBtn = screen.getByText(/Começar Jornada/i);
    fireEvent.click(ctaBtn);
    expect(mockNavigate).toHaveBeenCalledWith('/login?mode=register');
  });
});
