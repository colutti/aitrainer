export interface UserProfile {
  gender: string;
  age: number;
  height: number;
  goal_type: 'lose' | 'gain' | 'maintain';
  target_weight?: number;
  weekly_rate: number;
  email: string;
  notes?: string;
  display_name?: string;
  photo_base64?: string;
  subscription_plan?: string;
  custom_message_limit?: number | null;
  messages_sent_this_month?: number;
  total_messages_sent?: number;
  current_billing_cycle_start?: string;
}

export type OnboardingData = Partial<UserProfile>;
