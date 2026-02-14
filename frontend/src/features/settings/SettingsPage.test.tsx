import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { useAuthStore } from '../../shared/hooks/useAuth';

import { SettingsPage } from './SettingsPage';

vi.mock('../../shared/hooks/useAuth');

describe('SettingsPage', () => {
  it('should render user info and navigation tabs', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      userInfo: {
        id: '1',
        name: 'Test User',
        email: 'test@example.com',
      },
    });

    render(
      <MemoryRouter>
        <SettingsPage />
      </MemoryRouter>
    );

    // Header
    expect(screen.getByText('Configurações')).toBeInTheDocument();

    // User Info (now appears twice - once on desktop, once on mobile)
    expect(screen.getAllByText('Test User').length).toBeGreaterThan(0);
    expect(screen.getAllByText('test@example.com').length).toBeGreaterThan(0);
    expect(screen.getAllByText('T').length).toBeGreaterThan(0); // Initial

    // Navigation Tabs
    expect(screen.getByText('Perfil Pessoal')).toBeInTheDocument();
    expect(screen.getByText('Memórias')).toBeInTheDocument();
    expect(screen.getByText('Treinador AI')).toBeInTheDocument();
    expect(screen.getByText('Integrações')).toBeInTheDocument();
  });

  describe('Responsive Layout Tests', () => {
    beforeEach(() => {
      vi.mocked(useAuthStore).mockReturnValue({
        userInfo: {
          id: '1',
          name: 'Test User',
          email: 'test@example.com',
        },
      });
    });

    it('should render horizontal tab navigation at the top', () => {
      render(
        <MemoryRouter>
          <SettingsPage />
        </MemoryRouter>
      );

      // Verify navigation element exists and is horizontal (not a sidebar)
      const navElement = screen.getByRole('navigation');
      expect(navElement).toBeInTheDocument();

      // Verify all 4 tabs are visible
      expect(screen.getByText('Perfil Pessoal')).toBeInTheDocument();
      expect(screen.getByText('Memórias')).toBeInTheDocument();
      expect(screen.getByText('Treinador AI')).toBeInTheDocument();
      expect(screen.getByText('Integrações')).toBeInTheDocument();

      // Verify navigation has horizontal layout (flex class indicates flex-row by default)
      // The component now uses a horizontal layout with flex gap and flex-direction default (row)
      expect(navElement).toHaveClass('flex');
      expect(navElement).not.toHaveClass('flex-col');
    });

    it('should have user info accessible on all screen sizes', () => {
      render(
        <MemoryRouter>
          <SettingsPage />
        </MemoryRouter>
      );

      // Verify user info is accessible (appears in both desktop and mobile versions)
      const userInfoElements = screen.getAllByText('Test User');
      expect(userInfoElements.length).toBeGreaterThan(0);

      // Verify all user info elements are accessible regardless of screen size
      expect(screen.getAllByText('Test User').length).toBeGreaterThan(0);
      expect(screen.getAllByText('test@example.com').length).toBeGreaterThan(0);

      // Verify user initial avatar is visible (appears in both desktop and mobile)
      const avatarElements = screen.getAllByText('T');
      expect(avatarElements.length).toBeGreaterThan(0);
      avatarElements.forEach(el => expect(el).toBeVisible());

      // Verify user info mobile container exists
      const userInfoContainer = screen.getByTestId('user-info-container');
      expect(userInfoContainer).toBeInTheDocument();
    });
  });
});
