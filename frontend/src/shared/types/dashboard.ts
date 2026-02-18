export interface DashboardStats {
  metabolism: {
    tdee: number;
    daily_target: number;
    confidence: string;
    weekly_change: number;
    energy_balance: number;
    status: string;
    macro_targets?: {
      protein: number;
      carbs: number;
      fat: number;
    } | null;
    goal_type: string;
    consistency_score: number;
  };
  body: {
    weight_current: number;
    weight_diff: number;
    weight_diff_15?: number | null;
    weight_diff_30?: number | null;
    weight_trend: 'up' | 'down' | 'stable';
    body_fat_pct?: number | null;
    muscle_mass_pct?: number | null;
    muscle_mass_kg?: number | null;
    fat_diff?: number | null;
    fat_diff_15?: number | null;
    fat_diff_30?: number | null;
    muscle_diff?: number | null;
    muscle_diff_15?: number | null;
    muscle_diff_30?: number | null;
    bmr?: number | null;
  };
  calories: {
    consumed: number;
    target: number;
    percent: number;
  };
  workouts: {
    completed: number;
    target: number;
    lastWorkoutDate?: string;
  };
}

export interface RecentActivity {
  id: string;
  type: 'workout' | 'nutrition' | 'body';
  title: string;
  subtitle: string;
  date: string;
  icon?: string;
}

export interface WeightHistoryPoint {
  date: string;
  weight: number;
}

export interface TrendPoint {
  date: string;
  value: number;
}

export interface StreakStats {
  current_weeks: number;
  current_days: number;
  last_activity_date?: string;
}

export interface PRRecord {
  id: string;
  exercise: string;
  weight: number;
  reps: number;
  date: string;
  previous_weight?: number;
}

export interface StrengthRadarData {
  push: number;
  pull: number;
  legs: number;
  core?: number;
}

export interface DashboardData {
  stats: DashboardStats;
  recentActivities: RecentActivity[];
  weightHistory?: WeightHistoryPoint[];
  weightTrend?: TrendPoint[];
  fatHistory?: TrendPoint[];
  fatTrend?: TrendPoint[];
  muscleHistory?: TrendPoint[];
  muscleTrend?: TrendPoint[];
  streak?: StreakStats;
  recentPRs?: PRRecord[];
  strengthRadar?: StrengthRadarData;
  volumeTrend?: number[];
  weeklyFrequency?: boolean[];
}
