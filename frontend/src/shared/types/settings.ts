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
  trainer_id: string;
  name: string;
  avatar_url: string;
  short_description: string;
  catchphrase: string;
  specialties: string[];
}

export interface TrainerProfile {
  trainer_type: string;
}
