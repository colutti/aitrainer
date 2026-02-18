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

  // ─── weekly_rate select ─────────────────────────────────────────────────────

  it('weekly_rate should render as a select element', async () => {
    (settingsApi.getProfile as any).mockResolvedValue(mockProfile);
    render(<UserProfilePage />);

    await waitFor(() => screen.getByLabelText(/Meta Semanal/i));

    const weeklyRateField = screen.getByLabelText(/Meta Semanal/i);
    expect(weeklyRateField.tagName).toBe('SELECT');
  });

  it('weekly_rate select should contain the predefined rate options', async () => {
    (settingsApi.getProfile as any).mockResolvedValue(mockProfile);
    render(<UserProfilePage />);

    await waitFor(() => screen.getByLabelText(/Meta Semanal/i));

    const select = screen.getByLabelText(/Meta Semanal/i);
    const values = Array.from(select.querySelectorAll('option')).map((o) => o.getAttribute('value'));

    expect(values).toEqual(['0.25', '0.5', '0.75', '1', '1.5', '2']);
  });

  it('weekly_rate select should be disabled when goal_type is maintain', async () => {
    const maintainProfile = { ...mockProfile, goal_type: 'maintain', weekly_rate: 0 };
    (settingsApi.getProfile as any).mockResolvedValue(maintainProfile);
    render(<UserProfilePage />);

    await waitFor(() => screen.getByLabelText(/Meta Semanal/i));

    expect(screen.getByLabelText(/Meta Semanal/i)).toBeDisabled();
  });

  it('weekly_rate select should be enabled and set to 0.5 when switching from maintain to lose', async () => {
    const maintainProfile = { ...mockProfile, goal_type: 'maintain', weekly_rate: 0 };
    (settingsApi.getProfile as any).mockResolvedValue(maintainProfile);
    render(<UserProfilePage />);

    await waitFor(() => screen.getByLabelText(/Meta Semanal/i));

    // Change goal_type from maintain to lose
    const goalTypeSelect = screen.getByRole('combobox', { name: /Tipo de Objetivo/i });
    fireEvent.change(goalTypeSelect, { target: { value: 'lose' } });

    await waitFor(() => {
      const weeklyRate = screen.getByLabelText(/Meta Semanal/i);
      expect(weeklyRate).not.toBeDisabled();
      expect(weeklyRate).toHaveValue('0.5');
    });
  });

  // ─── target_weight validation ────────────────────────────────────────────────

  it('empty target_weight should submit as undefined without triggering generic error', async () => {
    const profileWithTarget = { ...mockProfile, goal_type: 'lose', weekly_rate: 0.5, target_weight: 70 };
    (settingsApi.getProfile as any).mockResolvedValue(profileWithTarget);
    (settingsApi.updateProfile as any).mockResolvedValue(profileWithTarget);

    render(<UserProfilePage />);

    await waitFor(() => screen.getByLabelText(/Peso Alvo/i));

    // Clear the target_weight field
    const targetWeightInput = screen.getByLabelText(/Peso Alvo/i);
    fireEvent.change(targetWeightInput, { target: { value: '' } });

    fireEvent.click(screen.getByRole('button', { name: /Salvar Alterações/i }));

    await waitFor(() => {
      expect(settingsApi.updateProfile).toHaveBeenCalledWith(
        expect.objectContaining({ target_weight: undefined })
      );
      expect(mockNotify.error).not.toHaveBeenCalled();
    });
  });

  it('should submit goal_type and weekly_rate changes correctly', async () => {
    // Regression: goal_type and weekly_rate must be sent to updateProfile.
    // Previously these could revert after page refresh due to a race condition
    // between updateProfile and updateIdentity (both called via Promise.all).
    // Fix: updateIdentity now uses targeted partial update on the backend,
    // so it no longer overwrites concurrent profile field changes.
    const profileWithLose = { ...mockProfile, goal_type: 'lose', weekly_rate: 0.5 };
    (settingsApi.getProfile as any).mockResolvedValue(profileWithLose);
    (settingsApi.updateProfile as any).mockResolvedValue(profileWithLose);

    render(<UserProfilePage />);

    await waitFor(() => screen.getByLabelText(/Meta Semanal/i));

    // Change goal_type to 'gain'
    const goalTypeSelect = screen.getByRole('combobox', { name: /Tipo de Objetivo/i });
    fireEvent.change(goalTypeSelect, { target: { value: 'gain' } });

    // Change weekly_rate to a valid select option
    const weeklyRateSelect = screen.getByLabelText(/Meta Semanal/i);
    fireEvent.change(weeklyRateSelect, { target: { value: '0.75' } });

    const submitButton = screen.getByRole('button', { name: /Salvar Alterações/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(settingsApi.updateProfile).toHaveBeenCalledWith(
        expect.objectContaining({ goal_type: 'gain', weekly_rate: 0.75 })
      );
    });
  });
});
