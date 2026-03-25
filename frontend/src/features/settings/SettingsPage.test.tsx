import { describe, it, expect } from 'vitest';

import { render, screen } from '../../shared/utils/test-utils';

import SettingsPage from './SettingsPage';

describe('SettingsPage', () => {
  it('should render settings header and tabs', () => {
    render(<SettingsPage />);
    
    expect(screen.getByText(/Gerencie sua conta e preferências/i)).toBeInTheDocument();
    expect(screen.getByText(/Configurações/i)).toBeInTheDocument();
    
    // Check for some tabs
    expect(screen.getByText(/Perfil Pessoal/i)).toBeInTheDocument();
    expect(screen.getByText(/Assinatura/i)).toBeInTheDocument();
    expect(screen.getByText(/Memórias/i)).toBeInTheDocument();
  });
});
