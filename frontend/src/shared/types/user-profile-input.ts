export interface UserProfileInput {
  gender: string;
  age: number;
  weight: number;
  height: number;
  goal?: string;
  goal_type: 'lose' | 'gain' | 'maintain';
  target_weight?: number;
  weekly_rate: number;
  notes?: string;
}
