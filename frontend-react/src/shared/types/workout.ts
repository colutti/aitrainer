/**
 * Workout data models for the frontend.
 */

export interface Exercise {
  name: string;
  sets: number;
  reps_per_set: number[];
  weights_per_set: number[];
}

export interface Workout {
  id: string;
  date: string;
  workout_type: string | null;
  exercises: Exercise[];
  duration_minutes: number | null;
}

export interface WorkoutListResponse {
  workouts: Workout[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
