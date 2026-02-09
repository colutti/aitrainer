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
    
    // User Info
    expect(screen.getByText('Test User')).toBeInTheDocument();
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
    expect(screen.getByText('T')).toBeInTheDocument(); // Initial

    // Navigation Tabs
    expect(screen.getByText('Perfil Pessoal')).toBeInTheDocument();
    expect(screen.getByText('Memórias')).toBeInTheDocument();
    expect(screen.getByText('Treinador AI')).toBeInTheDocument();
    expect(screen.getByText('Integrações')).toBeInTheDocument();
  });
});
