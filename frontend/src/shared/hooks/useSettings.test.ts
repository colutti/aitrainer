import { describe, expect, it, vi, beforeEach } from 'vitest';

import { httpClient } from '../api/http-client';
import type { UserProfile, TrainerProfile, TrainerCard } from '../types/settings';

import { useSettingsStore } from './useSettings';

// Mock httpClient
vi.mock('../api/http-client', () => ({
  httpClient: vi.fn(),
}));

describe('useSettingsStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useSettingsStore.getState().reset();
  });

  const mockProfile: UserProfile = { 
    email: 'test@example.com', 
    gender: 'Masculino', 
    age: 30, 
    weight: 80, 
    height: 180, 
    goal: 'muscle_gain',
    goal_type: 'gain',
    weekly_rate: 0.5
  };

  const mockTrainer: TrainerProfile = { 
    trainer_type: 'expert'
  };

  it('should have initial state', () => {
    const state = useSettingsStore.getState();
    expect(state.profile).toBeNull();
    expect(state.availableTrainers).toEqual([]);
    expect(state.isLoading).toBe(false);
    expect(state.isSaving).toBe(false);
    expect(state.error).toBeNull();
  });

  describe('fetchProfile', () => {
    it('should fetch profile successfully', async () => {
      vi.mocked(httpClient).mockResolvedValue(mockProfile);
      await useSettingsStore.getState().fetchProfile();
      const state = useSettingsStore.getState();
      expect(state.profile).toEqual(mockProfile);
      expect(state.isLoading).toBe(false);
    });

    it('should handle profile fetch returning undefined', async () => {
      vi.mocked(httpClient).mockResolvedValue(undefined);
      await useSettingsStore.getState().fetchProfile();
      const state = useSettingsStore.getState();
      expect(state.profile).toBeNull();
    });

    it('should handle fetch profile error', async () => {
      vi.mocked(httpClient).mockRejectedValue(new Error('error'));
      await useSettingsStore.getState().fetchProfile();
      const state = useSettingsStore.getState();
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe('Falha ao carregar perfil.');
    });
  });

  describe('updateProfile', () => {
    it('should update profile successfully', async () => {
      const updatedProfile = { ...mockProfile, goal: 'lose_weight', goal_type: 'lose' as const };
      vi.mocked(httpClient).mockResolvedValue(updatedProfile);
      await useSettingsStore.getState().updateProfile({ goal: 'lose_weight', goal_type: 'lose' });
      const state = useSettingsStore.getState();
      expect(state.profile).toEqual(updatedProfile);
      expect(state.isSaving).toBe(false);
    });

    it('should handle update profile returning undefined (keep existing)', async () => {
      useSettingsStore.setState({ profile: mockProfile });
      vi.mocked(httpClient).mockResolvedValue(undefined);
      await useSettingsStore.getState().updateProfile({ goal: 'lose_weight' });
      const state = useSettingsStore.getState();
      expect(state.profile).toEqual(mockProfile);
    });

    it('should handle update profile error', async () => {
      vi.mocked(httpClient).mockRejectedValue(new Error('error'));
      await expect(useSettingsStore.getState().updateProfile({ goal: 'lose_weight' }))
        .rejects.toThrow('error');
      const state = useSettingsStore.getState();
      expect(state.error).toBe('Falha ao salvar perfil.');
    });
  });

  describe('fetchTrainer', () => {
    it('should fetch trainer successfully', async () => {
      vi.mocked(httpClient).mockResolvedValue(mockTrainer);
      await useSettingsStore.getState().fetchTrainer();
      const state = useSettingsStore.getState();
      expect(state.trainer).toEqual(mockTrainer);
    });

    it('should handle trainer fetch returning undefined', async () => {
      vi.mocked(httpClient).mockResolvedValue(undefined);
      await useSettingsStore.getState().fetchTrainer();
      const state = useSettingsStore.getState();
      expect(state.trainer).toBeNull();
    });

    it('should handle fetch trainer error', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined);
      vi.mocked(httpClient).mockRejectedValue(new Error('error'));
      await useSettingsStore.getState().fetchTrainer();
      expect(consoleSpy).toHaveBeenCalledWith('Error fetching trainer:', expect.any(Error));
      consoleSpy.mockRestore();
    });
  });

  describe('fetchAvailableTrainers', () => {
    it('should fetch available trainers successfully', async () => {
      const mockTrainers: TrainerCard[] = [{ 
        trainer_id: '1', 
        name: 'T1', 
        avatar_url: '/url', 
        short_description: 'desc', 
        catchphrase: 'catch', 
        specialties: ['s1'] 
      }];
      vi.mocked(httpClient).mockResolvedValue(mockTrainers);
      await useSettingsStore.getState().fetchAvailableTrainers();
      const state = useSettingsStore.getState();
      expect(state.availableTrainers).toEqual(mockTrainers);
    });

    it('should handle available trainers returning undefined', async () => {
      vi.mocked(httpClient).mockResolvedValue(undefined);
      await useSettingsStore.getState().fetchAvailableTrainers();
      const state = useSettingsStore.getState();
      expect(state.availableTrainers).toEqual([]);
    });

    it('should handle fetch available trainers error', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined);
      vi.mocked(httpClient).mockRejectedValue(new Error('error'));
      await useSettingsStore.getState().fetchAvailableTrainers();
      expect(consoleSpy).toHaveBeenCalledWith('Error fetching available trainers:', expect.any(Error));
      consoleSpy.mockRestore();
    });
  });

  describe('updateTrainer', () => {
    it('should update trainer successfully', async () => {
      vi.mocked(httpClient).mockResolvedValue(mockTrainer);
      await useSettingsStore.getState().updateTrainer('expert');
      const state = useSettingsStore.getState();
      expect(state.trainer).toEqual(mockTrainer);
      expect(state.isSaving).toBe(false);
    });

    it('should handle update trainer returning undefined', async () => {
      vi.mocked(httpClient).mockResolvedValue(undefined);
      await useSettingsStore.getState().updateTrainer('expert');
      const state = useSettingsStore.getState();
      expect(state.trainer).toBeNull();
    });

    it('should handle update trainer error', async () => {
      vi.mocked(httpClient).mockRejectedValue(new Error('error'));
      await expect(useSettingsStore.getState().updateTrainer('expert'))
        .rejects.toThrow('error');
      const state = useSettingsStore.getState();
      expect(state.isSaving).toBe(false);
    });
  });

  it('should reset state', () => {
    useSettingsStore.setState({ profile: mockProfile, error: 'error' });
    useSettingsStore.getState().reset();
    const state = useSettingsStore.getState();
    expect(state.profile).toBeNull();
    expect(state.error).toBeNull();
  });
});
