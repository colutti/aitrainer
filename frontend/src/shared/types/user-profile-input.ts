export interface UserProfileInput {
  gender: string;
  age: number;
  height: number;
  goal_type: 'lose' | 'gain' | 'maintain';
  target_weight?: number;
  weekly_rate: number;
  notes?: string;
}
