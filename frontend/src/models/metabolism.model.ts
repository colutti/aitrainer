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
  latest_weight: number;
  outliers_count: number;
  weight_logs_count: number;
  nutrition_logs_count: number;
  confidence_reason?: string;
  message?: string;
  
  // Body Comp
  fat_change_kg?: number;
  lean_change_kg?: number;
  start_fat_pct?: number;
  end_fat_pct?: number;
  end_muscle_pct?: number;
  // Goal Tracking
  target_weight?: number;
  weeks_to_goal?: number;
  goal_eta_weeks?: number;
  weight_trend?: { date: string, weight: number }[];
  consistency?: { date: string, weight: boolean, nutrition: boolean }[];
}
