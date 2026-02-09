import { create } from 'zustand';

import { httpClient } from '../api/http-client';
import type { 
  UserProfile, 
  TrainerProfile, 
  TrainerCard 
} from '../types/settings';

interface SettingsState {
  profile: UserProfile | null;
  trainer: TrainerProfile | null;
  availableTrainers: TrainerCard[];
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
}

interface SettingsActions {
  fetchProfile: () => Promise<void>;
  updateProfile: (data: Partial<UserProfile>) => Promise<void>;
  fetchTrainer: () => Promise<void>;
  fetchAvailableTrainers: () => Promise<void>;
  updateTrainer: (trainerType: string) => Promise<void>;
  reset: () => void;
}

type SettingsStore = SettingsState & SettingsActions;

/**
 * Settings store using Zustand
 * 
 * Manages user profile, fitness goals, and trainer preferences.
 */
export const useSettingsStore = create<SettingsStore>((set, get) => ({
  profile: null,
  trainer: null,
  availableTrainers: [],
  isLoading: false,
  isSaving: false,
  error: null,

  fetchProfile: async () => {
    set({ isLoading: true, error: null });
    try {
      const profile = await httpClient<UserProfile>('/user/profile');
      set({ profile: profile ?? null, isLoading: false });
    } catch (error) {
      console.error('Error fetching profile:', error);
      set({ isLoading: false, error: 'Falha ao carregar perfil.' });
    }
  },

  updateProfile: async (data: Partial<UserProfile>) => {
    set({ isSaving: true, error: null });
    try {
      const updated = await httpClient<UserProfile>('/user/update_profile', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      set({ profile: updated ?? get().profile, isSaving: false });
    } catch (error) {
      console.error('Error updating profile:', error);
      set({ isSaving: false, error: 'Falha ao salvar perfil.' });
      throw error;
    }
  },

  fetchTrainer: async () => {
    try {
      const trainer = await httpClient<TrainerProfile>('/trainer/trainer_profile');
      set({ trainer: trainer ?? null });
    } catch (error) {
      console.error('Error fetching trainer:', error);
    }
  },

  fetchAvailableTrainers: async () => {
    try {
      const trainers = await httpClient<TrainerCard[]>('/trainer/available_trainers');
      set({ availableTrainers: trainers ?? [] });
    } catch (error) {
      console.error('Error fetching available trainers:', error);
    }
  },

  updateTrainer: async (trainerType: string) => {
    set({ isSaving: true });
    try {
      const updated = await httpClient<TrainerProfile>('/trainer/update_trainer_profile', {
        method: 'PUT',
        body: JSON.stringify({ trainer_type: trainerType }),
      });
      set({ trainer: updated ?? null, isSaving: false });
    } catch (error) {
      console.error('Error updating trainer:', error);
      set({ isSaving: false });
      throw error;
    }
  },

  reset: () => {
    set({
      profile: null,
      trainer: null,
      availableTrainers: [],
      isLoading: false,
      isSaving: false,
      error: null,
    });
  },
}));
