export interface WeightLog {
  user_email: string;
  date: string; // ISO date string YYYY-MM-DD
  weight_kg: number;
  notes?: string;
}
