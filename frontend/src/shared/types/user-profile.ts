export interface UserProfile {
  gender: string;
  age: number;
  weight: number;
  height: number;
  goal?: string;
  goal_type: 'lose' | 'gain' | 'maintain';
  target_weight?: number;
  weekly_rate: number;
  email: string;
  notes?: string;
}

export type OnboardingData = Partial<UserProfile>;
