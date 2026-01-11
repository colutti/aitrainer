export interface MetabolismResponse {
  tdee: number;
  confidence: 'high' | 'medium' | 'low' | 'none';
  avg_calories: number;
  weight_change_per_week: number;
  logs_count: number;
  startDate: string;
  endDate: string;
  start_weight: number;
  end_weight: number;
  daily_target: number;
  goal_weekly_rate: number;
  goal_type: string;
  status: string;
  energy_balance: number;
  is_stable: boolean;
  message?: string;
}
