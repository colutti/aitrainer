import { describe, expect, it } from 'vitest';

import type { WorkoutLog } from '../types/workout';

import { mapWorkoutLogToWorkout } from './workout-mapper';

describe('workout-mapper', () => {
  it('should map WorkoutLog with existing notes correctly', () => {
    const mockLog: WorkoutLog = {
      id: '1',
      user_email: 'test@test.com',
      date: '2024-01-01',
      workout_type: 'Legs',
      notes: 'My own notes',
      exercises: [],
      source: 'hevy',
      duration_minutes: 60,
      external_id: '123',
      created_at: '2024-01-01',
      updated_at: '2024-01-01'
    };

    const result = mapWorkoutLogToWorkout(mockLog);
    expect(result.notes).toBe('My own notes');
  });

  it('should generate Hevy sync note if notes missing', () => {
    const mockLog: WorkoutLog = {
      id: '1',
      user_email: 'test@test.com',
      date: '2024-01-01',
      workout_type: 'Legs',
      exercises: [],
      source: 'hevy',
      external_id: 'ext-123',
      duration_minutes: 60,
      notes: null,
      created_at: '2024-01-01',
      updated_at: '2024-01-01'
    };

    const result = mapWorkoutLogToWorkout(mockLog);
    expect(result.notes).toBe('Sincronizado via Hevy. ext-123');
  });

  it('should handle Hevy source without external_id', () => {
    const mockLog: WorkoutLog = {
      id: '1',
      user_email: 'test@test.com',
      date: '2024-01-01',
      workout_type: 'Legs',
      exercises: [],
      source: 'hevy',
      duration_minutes: 60,
      notes: null,
      external_id: null,
      created_at: '2024-01-01',
      updated_at: '2024-01-01'
    };

    const result = mapWorkoutLogToWorkout(mockLog);
    expect(result.notes).toBe('Sincronizado via Hevy. ');
  });

  it('should return undefined notes if source is not hevy and notes missing', () => {
    const mockLog: WorkoutLog = {
      id: '1',
      user_email: 'test@test.com',
      date: '2024-01-01',
      workout_type: 'Legs',
      exercises: [],
      source: 'manual',
      duration_minutes: 60,
      notes: null,
      external_id: null,
      created_at: '2024-01-01',
      updated_at: '2024-01-01'
    };

    const result = mapWorkoutLogToWorkout(mockLog);
    expect(result.notes).toBeUndefined();
  });

  it('should handle missing weights for sets', () => {
    const mockLog: WorkoutLog = {
      id: '1',
      user_email: 'test@test.com',
      date: '2024-01-01',
      workout_type: 'Chest',
      created_at: '2024-01-01',
      updated_at: '2024-01-01',
      duration_minutes: 30,
      source: 'manual',
      notes: null,
      external_id: null,
      exercises: [
        {
          name: 'Pushup',
          sets: 2,
          reps_per_set: [10, 10], // 2 sets
          weights_per_set: [0],   // Only 1 weight provided
        }
      ]
    };

    const result = mapWorkoutLogToWorkout(mockLog);
    expect(result.exercises[0]!.sets[0]!.weight_kg).toBe(0);
    expect(result.exercises[0]!.sets[1]!.weight_kg).toBeUndefined();
  });
});
