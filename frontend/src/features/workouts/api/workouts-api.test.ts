import { describe, expect, it, vi, beforeEach } from 'vitest';

import { httpClient } from '../../../shared/api/http-client';

import { workoutsApi } from './workouts-api';

vi.mock('../../../shared/api/http-client', () => ({
  httpClient: vi.fn(),
}));

describe('workoutsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch paginated workouts', async () => {
    const mockResponse = {
      workouts: [{ id: '1', date: '2024-01-01', exercises: [] }],
      total: 50,
      page: 2,
      page_size: 20,
      total_pages: 3
    };
    vi.mocked(httpClient).mockResolvedValue(mockResponse);
    
    const res = await workoutsApi.getWorkouts(2, 20);
    expect(res).toEqual(mockResponse);
    expect(httpClient).toHaveBeenCalledWith('/workout/list?page=2&page_size=20');
  });

  it('should fetch workout by id', async () => {
    const mockWorkout = { id: '123', date: '2024-01-01', exercises: [] };
    vi.mocked(httpClient).mockResolvedValue(mockWorkout);
    
    await workoutsApi.getWorkoutById('123');
    expect(httpClient).toHaveBeenCalledWith('/workout/123');
  });

  it('should delete workout', async () => {
    await workoutsApi.deleteWorkout('123');
    expect(httpClient).toHaveBeenCalledWith('/workout/123', { method: 'DELETE' });
  });

  it('should create a manual workout', async () => {
    const payload = {
      date: '2024-01-01',
      workout_type: 'Push',
      duration_minutes: 45,
      source: 'manual' as const,
      exercises: [
        {
          name: 'Bench Press',
          sets: 2,
          reps_per_set: [10, 8],
          weights_per_set: [60, 70],
        },
      ],
    };

    vi.mocked(httpClient).mockResolvedValue({ id: 'workout-1', ...payload });

    await workoutsApi.createWorkout(payload);

    expect(httpClient).toHaveBeenCalledWith('/workout', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  });

  it('should fetch workout types', async () => {
    vi.mocked(httpClient).mockResolvedValue(['Push', 'Pull']);

    const result = await workoutsApi.getWorkoutTypes();

    expect(result).toEqual(['Push', 'Pull']);
    expect(httpClient).toHaveBeenCalledWith('/workout/types');
  });

  it('should fetch exercise suggestions', async () => {
    vi.mocked(httpClient).mockResolvedValue(['Bench Press', 'Squat']);

    const result = await workoutsApi.getExerciseSuggestions();

    expect(result).toEqual(['Bench Press', 'Squat']);
    expect(httpClient).toHaveBeenCalledWith('/workout/exercises');
  });
});
