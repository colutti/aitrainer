export interface TrainerProfile {
  user_email?: string;
  trainer_type: string;
}

export interface TrainerCard {
  trainer_id: string;
  name: string;
  gender: string;
  avatar_url: string;
  short_description: string;
  catchphrase: string;
  specialties: string[];
}