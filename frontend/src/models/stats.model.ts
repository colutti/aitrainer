export interface PersonalRecord {
  exercise_name: string;
  weight: number;
  reps: number;
  date: string;
  workout_id: string;
}

export interface VolumeStat {
  category: string;
  volume: number;
}

export interface WorkoutWithId {
  id: string;
  user_email: string;
  date: string; // ISO date
  workout_type: string | null;
  duration_minutes: number | null;
}

export interface WorkoutStats {
  current_streak_weeks: number;
  weekly_frequency: boolean[];
  weekly_volume: VolumeStat[];
  recent_prs: PersonalRecord[];
  total_workouts: number;
  last_workout: WorkoutWithId | null;
}
