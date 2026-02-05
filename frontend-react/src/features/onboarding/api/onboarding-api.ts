import { httpClient } from '../../../shared/api/http-client';
import { OnboardingData } from '../../../shared/types/user-profile'; // Or define locally

// Need to check where OnboardingData is defined, probably better to define here or in types

export interface OnboardingPayload {
  token: string;
  password?: string;
  gender: string;
  age: number;
  weight: number;
  height: number;
  goal_type: string;
  weekly_rate: number;
  trainer_type: string;
  activity_level?: string;
  name?: string;
}

export interface TokenValidationResponse {
  valid: boolean;
  reason?: 'not_found' | 'expired' | 'already_used';
  email?: string;
}

export interface CompleteResponse {
  token: string;
}

export const onboardingApi = {
  validateToken: async (token: string): Promise<TokenValidationResponse> => {
     return httpClient(`/onboarding/validate?token=${token}`);
  },

  completeOnboarding: async (data: OnboardingPayload): Promise<CompleteResponse> => {
    return httpClient('/onboarding/complete', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
};
