export interface NutritionLog {
  id: string;
  user_email: string;
  date: string;
  calories: number;
  protein_grams: number;
  carbs_grams: number;
  fat_grams: number;
  fiber_grams?: number;
  sugar_grams?: number;
  sodium_mg?: number;
  cholesterol_mg?: number;
  source: string;
  notes?: string;
}

export interface DailyMacros {
  date: string;
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
}

export interface NutritionStats {
  today: NutritionLog | null;
  weekly_adherence: boolean[];
  last_7_days: DailyMacros[];
  avg_daily_calories: number;
  avg_daily_calories_14_days: number;
  avg_protein: number;
  total_logs: number;
  tdee?: number;
  daily_target?: number;
  macro_targets?: {
    protein: number;
    carbs: number;
    fat: number;
  };
  stability_score?: number;
  last_14_days: DailyMacros[];
}

export interface NutritionListResponse {
  logs: NutritionLog[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CreateNutritionLogRequest {
  date: string;
  source: string;
  calories: number;
  protein_grams: number;
  carbs_grams: number;
  fat_grams: number;
  fiber_grams?: number;
  sodium_mg?: number;
}
