import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { SettingsPage } from './SettingsPage';

describe('SettingsPage', () => {
  it('should render header and navigation tabs', () => {
    render(
      <MemoryRouter>
        <SettingsPage />
      </MemoryRouter>
    );

    // Header
    expect(screen.getByText('Configurações')).toBeInTheDocument();
    expect(screen.getByText('Gerencie seu perfil e preferências do app.')).toBeInTheDocument();

    // Navigation Tabs
    expect(screen.getByText('Perfil Pessoal')).toBeInTheDocument();
    expect(screen.getByText('Memórias')).toBeInTheDocument();
    expect(screen.getByText('Treinador AI')).toBeInTheDocument();
    expect(screen.getByText('Integrações')).toBeInTheDocument();
  });

  it('should render horizontal tab navigation', () => {
    render(
      <MemoryRouter>
        <SettingsPage />
      </MemoryRouter>
    );

    // Verify navigation element exists and is horizontal
    const navElement = screen.getByRole('navigation');
    expect(navElement).toBeInTheDocument();
    expect(navElement).toHaveClass('flex');
    expect(navElement).not.toHaveClass('flex-col');
  });
});
