export interface UserProfile {
  email: string;
  gender: string;
  age: number;
  height: number;
  notes?: string;
  display_name?: string;
  photo_base64?: string;
  subscription_plan?: string;
  custom_message_limit?: number | null;
  custom_trial_days?: number | null;
  messages_sent_this_month?: number;
  total_messages_sent?: number;
  current_billing_cycle_start?: string;
  messages_sent_today?: number;
  last_message_date?: string;
  trial_remaining_days?: number | null;
  current_daily_limit?: number | null;
  current_plan_limit?: number | null;
  effective_remaining_messages?: number;
  onboarding_completed?: boolean;
  is_demo?: boolean;
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
