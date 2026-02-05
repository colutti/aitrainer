export interface WeightLog {
  date: string;
  weight_kg: number;
  body_fat_pct?: number;
  muscle_mass_pct?: number;
  bone_mass_kg?: number;
  body_water_pct?: number;
  visceral_fat?: number;
  bmr?: number;
  bmi?: number;
  source?: string;
  notes?: string;
  user_email: string;
  trend_weight?: number;
}

export interface WeightTrendPoint {
  date: string;
  value: number | null;
}

export interface BodyCompositionStats {
  latest: WeightLog | null;
  weight_trend: WeightTrendPoint[];
  fat_trend: WeightTrendPoint[];
  muscle_trend: WeightTrendPoint[];
}
