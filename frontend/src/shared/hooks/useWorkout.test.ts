import { describe, expect, it, vi, beforeEach } from 'vitest';

import { httpClient } from '../api/http-client';
import type { WorkoutLog } from '../types/workout';

import { useWorkoutStore } from './useWorkout';

// Mock httpClient
vi.mock('../api/http-client', () => ({
  httpClient: vi.fn(),
}));

describe('useWorkoutStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useWorkoutStore.getState().reset();
  });

  const mockWorkouts: WorkoutLog[] = [
    { 
      id: '1', 
      workout_type: 'Strength', 
      date: '2024-01-01', 
      user_email: 'test@test.com', 
      source: 'app', 
      duration_minutes: 60, 
      exercises: [], 
      created_at: '2024-01-01', 
      updated_at: '2024-01-01',
      notes: null,
      external_id: null
    },
    { 
      id: '2', 
      workout_type: 'Cardio', 
      date: '2024-01-02', 
      user_email: 'test@test.com', 
      source: 'app', 
      duration_minutes: 30, 
      exercises: [], 
      created_at: '2024-01-02', 
      updated_at: '2024-01-02',
      notes: null,
      external_id: null
    },
  ];

  const mockResponse = {
    workouts: mockWorkouts,
    total: 2,
    page: 1,
    page_size: 20,
    total_pages: 1,
  };

  it('should have initial state', () => {
    const state = useWorkoutStore.getState();
    expect(state.workouts).toEqual([]);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  describe('fetchWorkouts', () => {
    it('should fetch workouts successfully', async () => {
      vi.mocked(httpClient).mockResolvedValue(mockResponse);

      await useWorkoutStore.getState().fetchWorkouts();

      const state = useWorkoutStore.getState();
      expect(state.workouts).toEqual(mockWorkouts);
      expect(state.total).toBe(2);
      expect(state.isLoading).toBe(false);
      expect(httpClient).toHaveBeenCalledWith('/workout/list?page=1&page_size=20');
    });

    it('should fetch workouts with pagination', async () => {
      vi.mocked(httpClient).mockResolvedValue({
        workouts: [],
        total: 0,
        page: 1,
        page_size: 20,
        total_pages: 0,
      });

      await useWorkoutStore.getState().fetchWorkouts(1);
      expect(httpClient).toHaveBeenCalledWith('/workout/list?page=1&page_size=20');
    });

    it('should handle undefined response', async () => {
      vi.mocked(httpClient).mockResolvedValue(undefined);
      
      await useWorkoutStore.getState().fetchWorkouts();
      const state = useWorkoutStore.getState();
      expect(state.isLoading).toBe(false);
      expect(state.workouts).toEqual([]);
    });

    it('should handle fetch workouts error', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      vi.mocked(httpClient).mockRejectedValue(new Error('failed'));

      await useWorkoutStore.getState().fetchWorkouts();

      const state = useWorkoutStore.getState();
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe('failed');
      consoleSpy.mockRestore();
    });
  });

  describe('deleteWorkout', () => {
    it('should delete workout successfully', async () => {
      useWorkoutStore.setState({ workouts: mockWorkouts, total: 2 });
      vi.mocked(httpClient).mockResolvedValue({});

      await useWorkoutStore.getState().deleteWorkout('1');

      const state = useWorkoutStore.getState();
      expect(state.workouts).toHaveLength(1);
      expect(state.workouts[0]!.id).toBe('2');
      expect(state.total).toBe(1);
      expect(httpClient).toHaveBeenCalledWith('/workout/1', { method: 'DELETE' });
    });

    it('should handle delete workout error', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      vi.mocked(httpClient).mockRejectedValue(new Error('failed'));

      await expect(useWorkoutStore.getState().deleteWorkout('1'))
        .rejects.toThrow('failed');

      const state = useWorkoutStore.getState();
      expect(state.isLoading).toBe(false);
      consoleSpy.mockRestore();
    });
  });

  it('should set selected workout', () => {
    const workout = { id: '1' } as WorkoutLog;
    useWorkoutStore.getState().setSelectedWorkout(workout);
    expect(useWorkoutStore.getState().selectedWorkout).toEqual(workout);
  });

  it('should reset state', () => {
    useWorkoutStore.setState({ workouts: mockWorkouts, isLoading: true });
    useWorkoutStore.getState().reset();
    const state = useWorkoutStore.getState();
    expect(state.workouts).toEqual([]);
    expect(state.isLoading).toBe(false);
  });

  it('should create a manual workout and prepend it to the store', async () => {
    const createdWorkout: WorkoutLog = {
      id: '3',
      user_email: 'test@test.com',
      date: '2024-01-03',
      workout_type: 'Push',
      exercises: [
        {
          name: 'Bench Press',
          sets: 2,
          reps_per_set: [10, 8],
          weights_per_set: [60, 70],
        },
      ],
      duration_minutes: 45,
      source: 'manual',
      external_id: null,
      notes: null,
      created_at: '2024-01-03',
      updated_at: '2024-01-03',
    };
    useWorkoutStore.setState({ workouts: mockWorkouts, total: 2 });
    vi.mocked(httpClient).mockResolvedValue(createdWorkout);

    await useWorkoutStore.getState().createWorkout({
      date: '2024-01-03',
      workout_type: 'Push',
      duration_minutes: 45,
      source: 'manual',
      exercises: [
        {
          name: 'Bench Press',
          sets: 2,
          reps_per_set: [10, 8],
          weights_per_set: [60, 70],
        },
      ],
    });

    const state = useWorkoutStore.getState();
    expect(state.workouts[0]).toEqual(createdWorkout);
    expect(state.total).toBe(3);
    expect(httpClient).toHaveBeenCalledWith('/workout', {
      method: 'POST',
      body: JSON.stringify({
        date: '2024-01-03',
        workout_type: 'Push',
        duration_minutes: 45,
        source: 'manual',
        exercises: [
          {
            name: 'Bench Press',
            sets: 2,
            reps_per_set: [10, 8],
            weights_per_set: [60, 70],
          },
        ],
      }),
    });
  });

  it('should fetch workout type suggestions', async () => {
    vi.mocked(httpClient).mockResolvedValue(['Push', 'Pull']);

    const result = await useWorkoutStore.getState().fetchWorkoutTypes();

    expect(result).toEqual(['Push', 'Pull']);
    expect(httpClient).toHaveBeenCalledWith('/workout/types');
  });

  it('should fetch exercise suggestions', async () => {
    vi.mocked(httpClient).mockResolvedValue(['Bench Press', 'Squat']);

    const result = await useWorkoutStore.getState().fetchExerciseSuggestions();

    expect(result).toEqual(['Bench Press', 'Squat']);
    expect(httpClient).toHaveBeenCalledWith('/workout/exercises');
  });
});
