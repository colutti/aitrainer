import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { useAuthStore } from '../../../shared/hooks/useAuth';
import { useNotificationStore } from '../../../shared/hooks/useNotification';
import { settingsApi } from '../api/settings-api';

import { UserProfilePage } from './UserProfilePage';

// Mock the API and Hook
vi.mock('../api/settings-api', () => ({
  settingsApi: {
    getProfile: vi.fn(),
    updateProfile: vi.fn(),
    updateIdentity: vi.fn(),
  },
}));

vi.mock('../../../shared/hooks/useNotification', () => ({
  useNotificationStore: vi.fn(),
}));

vi.mock('../../../shared/hooks/useAuth', () => ({
  useAuthStore: vi.fn(),
}));

describe('UserProfilePage', () => {
  const mockNotify = {
    success: vi.fn(),
    error: vi.fn(),
  };

  const mockProfile = {
    email: 'test@example.com',
    age: 25,
    weight: 70,
    height: 175,
    gender: 'Masc',
    goal_type: 'maintain',
    weekly_rate: 0,
    target_weight: 70,
    goal: 'Be healthy',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useNotificationStore).mockReturnValue(mockNotify as any);
    vi.mocked(useAuthStore).mockReturnValue({
      userInfo: { email: 'test@example.com' },
      loadUserInfo: vi.fn().mockResolvedValue(undefined),
      isAuthenticated: true,
    } as any);
    (settingsApi.updateIdentity as any).mockResolvedValue(undefined);
  });

  it('should render profile data correctly', async () => {
    (settingsApi.getProfile as any).mockResolvedValue(mockProfile);

    render(<UserProfilePage />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Email/i)).toHaveValue('test@example.com');
      expect(screen.getByLabelText(/Idade/i)).toHaveValue(25);
      expect(screen.getByLabelText(/Peso \(kg\)/i)).toHaveValue(70);
    });
  });

  it('should update profile successfully', async () => {
    (settingsApi.getProfile as any).mockResolvedValue(mockProfile);
    (settingsApi.updateProfile as any).mockResolvedValue({ ...mockProfile, age: 26 });

    render(<UserProfilePage />);

    await waitFor(() => screen.getByLabelText(/Idade/i));
    
    const ageInput = screen.getByLabelText(/Idade/i);
    fireEvent.change(ageInput, { target: { value: '26' } });
    
    const submitButton = screen.getByRole('button', { name: /Salvar Alterações/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(settingsApi.updateProfile).toHaveBeenCalledWith(expect.objectContaining({ age: 26 }));
      expect(mockNotify.success).toHaveBeenCalledWith('Perfil atualizado com sucesso!');
    });
  });

  it('should handle update error', async () => {
    (settingsApi.getProfile as any).mockResolvedValue(mockProfile);
    (settingsApi.updateProfile as any).mockRejectedValue(new Error('API Error'));

    render(<UserProfilePage />);

    await waitFor(() => screen.getByLabelText(/Idade/i));
    
    const submitButton = screen.getByRole('button', { name: /Salvar Alterações/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockNotify.error).toHaveBeenCalledWith('Erro ao atualizar perfil');
    });
  });

  it('should show validation errors', async () => {
    (settingsApi.getProfile as any).mockResolvedValue(mockProfile);
    render(<UserProfilePage />);

    await waitFor(() => screen.getByLabelText(/Idade/i));
    
    const ageInput = screen.getByLabelText(/Idade/i);
    fireEvent.change(ageInput, { target: { value: '0' } });
    
    const submitButton = screen.getByRole('button', { name: /Salvar Alterações/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Idade inválida/i)).toBeInTheDocument();
    });
  });
});
