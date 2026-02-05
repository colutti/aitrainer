/**
 * Workout data models for the frontend.
 */

export interface ExerciseLog {
  name: string;
  sets: number;
  reps_per_set: number[];
  weights_per_set: number[];
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
}

export interface WorkoutListResponse {
  workouts: WorkoutLog[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
