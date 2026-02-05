export interface UserProfile {
  gender: string;
  age: number;
  weight: number;
  height: number;
  goal: string;
  email: string;
  goal_type: 'lose' | 'gain' | 'maintain';
  weekly_rate: number;
  target_weight?: number;
  notes?: string;
  tdee?: number;
}

export interface TrainerCard {
  id: string;
  name: string;
  description: string;
  full_description: string;
  avatar_url: string;
  base_prompt: string;
}

export interface TrainerProfile {
  trainer_type: string;
}
