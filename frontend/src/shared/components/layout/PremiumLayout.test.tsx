import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';

import { useAuthStore } from '../../hooks/useAuth';

import { PremiumLayout } from './PremiumLayout';

// Mock do hook de autenticação
vi.mock('../../hooks/useAuth', () => ({
  useAuthStore: vi.fn(),
}));

describe('PremiumLayout', () => {
  it('applies the workspace width mode on dashboard route', () => {
    (useAuthStore as any).mockReturnValue({
      userInfo: { name: 'Atlas User', photo_base64: 'base64str', email: 'atlas@fityq.it' },
      logout: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <PremiumLayout />
      </MemoryRouter>
    );

    expect(screen.getByTestId('app-shell-main')).toHaveClass('max-w-[1920px]');
  });

  it('applies the conversation width mode on chat route', () => {
    (useAuthStore as any).mockReturnValue({
      userInfo: { name: 'Atlas User', photo_base64: 'base64str', email: 'atlas@fityq.it' },
      logout: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/dashboard/chat']}>
        <PremiumLayout />
      </MemoryRouter>
    );

    expect(screen.getByTestId('app-shell-main')).toHaveClass('max-w-[2160px]');
    expect(screen.getByTestId('desktop-nav')).not.toHaveClass('backdrop-blur-xl');
  });

  it('keeps mobile navigation rendered after shell redesign', () => {
    (useAuthStore as any).mockReturnValue({
      userInfo: { name: 'Atlas User', photo_base64: 'base64str', email: 'atlas@fityq.it' },
      logout: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/dashboard/chat']}>
        <PremiumLayout />
      </MemoryRouter>
    );

    expect(screen.getByTestId('mobile-nav')).toBeInTheDocument();
  });

  it('renders correctly with user info and displays top nav and mobile nav', () => {
    (useAuthStore as any).mockReturnValue({
      userInfo: { name: 'Colutti', photo_base64: 'base64str', email: 'colutti@fityq.it' },
    });

    render(
      <MemoryRouter>
        <PremiumLayout />
      </MemoryRouter>
    );

    // Header mobile e UserAvatar Desktop (usando regex para match parcial caso quebre)
    expect(screen.getAllByText(/Colutti/i).length).toBeGreaterThan(0);

    // Garante que o contrato E2E está sendo cumprido na navegação
    expect(screen.getByTestId('desktop-nav')).toBeInTheDocument();
    expect(screen.getByTestId('mobile-nav')).toBeInTheDocument();
    
    // Testa alguns sub-itens do E2E
    expect(screen.getByTestId('desktop-nav-home')).toBeInTheDocument();
    expect(screen.getByTestId('nav-home')).toBeInTheDocument();
  });

  it('renders gracefully without user photo', () => {
    (useAuthStore as any).mockReturnValue({
      userInfo: { name: 'Atlas User', email: 'atlas@fityq.it' },
    });

    render(
      <MemoryRouter>
        <PremiumLayout />
      </MemoryRouter>
    );

    // Como não tem foto, a letra inicial 'A' de 'Atlas User' deve ser renderizada (pelo menos duas vezes: mobile e desktop)
    const initials = screen.getAllByText('A');
    expect(initials.length).toBeGreaterThan(0);
  });

  it('shows demo badge and hides quick actions for demo users', () => {
    (useAuthStore as any).mockReturnValue({
      userInfo: { name: 'Demo User', email: 'demo@fityq.it', is_demo: true },
    });

    render(
      <MemoryRouter>
        <PremiumLayout />
      </MemoryRouter>
    );

    expect(screen.getAllByText(/Demo Read-Only/i).length).toBeGreaterThan(0);
    expect(screen.queryByTestId('quick-add-fab')).not.toBeInTheDocument();
  });

  it('renders logout action in the top navigation', () => {
    const logout = vi.fn();
    (useAuthStore as any).mockReturnValue({
      userInfo: { name: 'Logout User', email: 'logout@fityq.it' },
      logout,
    });

    render(
      <MemoryRouter>
        <PremiumLayout />
      </MemoryRouter>
    );

    expect(screen.getByTestId('desktop-logout')).toBeInTheDocument();
    expect(screen.getByTestId('mobile-logout')).toBeInTheDocument();
    expect(screen.getByLabelText('Logout')).toBeInTheDocument();
  });
});
