import type { Workout, WorkoutLog } from '../types/workout';

/**
 * Maps a WorkoutLog (from backend) to the Workout structure expected by the UI
 */
export function mapWorkoutLogToWorkout(log: WorkoutLog): Workout {
  return {
    id: log.id,
    user_email: log.user_email,
    date: log.date,
    workout_type: log.workout_type,
    duration_minutes: log.duration_minutes ?? undefined,
    notes: log.notes ?? (log.source === 'hevy' ? `Sincronizado via Hevy. ${log.external_id ?? ''}` : undefined),
    source: log.source ?? undefined,
    external_id: log.external_id ?? undefined,
    exercises: log.exercises.map((ex, idx) => ({
      exercise_id: `ex-${idx.toString()}`,
      exercise_title: ex.name,
      sets: ex.reps_per_set.map((reps, sIdx) => ({
        set_index: sIdx + 1,
        reps: reps || undefined,
        weight_kg: ex.weights_per_set[sIdx] ?? undefined,
        duration_seconds: ex.duration_seconds_per_set?.[sIdx] || undefined,
        distance_meters: ex.distance_meters_per_set?.[sIdx] || undefined,
      }))
    }))
  };
}
