export interface WeightLog {
  date: string;
  weight_kg: number;
  body_fat_pct?: number;
  muscle_mass_pct?: number;
  muscle_mass_kg?: number;
  bone_mass_kg?: number;
  body_water_pct?: number;
  visceral_fat?: number;
  bmr?: number;
  bmi?: number;
  
  // Body Measurements
  neck_cm?: number;
  chest_cm?: number;
  waist_cm?: number;
  hips_cm?: number;
  bicep_r_cm?: number;
  bicep_l_cm?: number;
  thigh_r_cm?: number;
  thigh_l_cm?: number;
  calf_r_cm?: number;
  calf_l_cm?: number;

  source?: string;
  notes?: string;
  user_email: string;
  trend_weight?: number;
  id?: string;
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

export interface WeightListResponse {
  logs: WeightLog[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
