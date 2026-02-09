/**
 * Extended workout type with exercise details for drawer view
 */
export interface WorkoutSet {
  set_index: number;
  weight_kg?: number;
  reps?: number;
  duration_seconds?: number;
  distance_meters?: number;
}

export interface WorkoutExercise {
  exercise_id?: string;
  exercise_title: string;
  sets: WorkoutSet[];
  notes?: string;
  pr_data?: Record<string, number>;
}

export interface Workout {
  id: string;
  user_email?: string;
  date: string;
  workout_type?: string | null;
  duration_minutes?: number;
  exercises: WorkoutExercise[];
  notes?: string;
  source?: string;
  external_id?: string;
}

export interface WorkoutLog {
  id: string;
  user_email: string;
  date: string;
  workout_type: string | null;
  exercises: ExerciseLog[];
  duration_minutes: number | null;
  source: string | null;
  external_id: string | null;
  notes: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface ExerciseLog {
  name: string;
  sets: number;
  reps_per_set: number[];
  weights_per_set: number[];
}

export interface WorkoutListResponse {
  workouts: WorkoutLog[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
