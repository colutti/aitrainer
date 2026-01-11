export interface WeightLog {
  user_email: string;
  date: string; // ISO date string YYYY-MM-DD
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
}

export interface BodyCompositionStats {
  latest: WeightLog | null;
  weight_trend: { date: string; value: number }[];
  fat_trend: { date: string; value: number }[];
  muscle_trend: { date: string; value: number }[];
}
