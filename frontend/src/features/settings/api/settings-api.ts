import { httpClient } from '../../../shared/api/http-client';
import type { TrainerProfile } from '../../../shared/types/trainer-profile';
import type { UserProfile } from '../../../shared/types/user-profile';

export const settingsApi = {
  getProfile: async (): Promise<UserProfile> => {
    return httpClient<UserProfile>('/user/profile') as Promise<UserProfile>;
  },
  
  updateProfile: async (data: Partial<UserProfile>): Promise<UserProfile> => {
    return httpClient<UserProfile>('/user/update_profile', {
      method: 'POST',
      body: JSON.stringify(data)
    }) as Promise<UserProfile>;
  },

  getTrainer: async (): Promise<TrainerProfile> => {
      return httpClient<TrainerProfile>('/trainer/trainer_profile') as Promise<TrainerProfile>;
  },

  updateTrainer: async (trainerType: string): Promise<TrainerProfile> => {
      return httpClient<TrainerProfile>('/trainer/update_trainer_profile', {
          method: 'PUT',
          body: JSON.stringify({ trainer_type: trainerType })
      }) as Promise<TrainerProfile>;
  }
};
