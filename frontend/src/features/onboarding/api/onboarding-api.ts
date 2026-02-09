import { httpClient } from '../../../shared/api/http-client';


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
     return httpClient<TokenValidationResponse>(`/onboarding/validate?token=${token}`) as Promise<TokenValidationResponse>;
  },

  completeOnboarding: async (data: OnboardingPayload): Promise<CompleteResponse> => {
    return httpClient<CompleteResponse>('/onboarding/complete', {
      method: 'POST',
      body: JSON.stringify(data)
    }) as Promise<CompleteResponse>;
  }
};
