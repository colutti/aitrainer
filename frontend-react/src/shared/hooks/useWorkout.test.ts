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

  it('should have initial state', () => {
    const state = useWorkoutStore.getState();
    expect(state.workouts).toEqual([]);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('should fetch workouts successfully', async () => {
    const mockResponse = {
      workouts: [
        { id: '1', date: '2024-01-01', workout_type: 'Legs', exercises: [] } as unknown as WorkoutLog,
      ],
      total: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
    };

    vi.mocked(httpClient).mockResolvedValue(mockResponse);

    await useWorkoutStore.getState().fetchWorkouts();

    const state = useWorkoutStore.getState();
    expect(state.workouts).toEqual(mockResponse.workouts);
    expect(state.total).toBe(1);
    expect(state.isLoading).toBe(false);
    // Use string matching for the URL as it includes query params
    expect(vi.mocked(httpClient)).toHaveBeenCalledWith(expect.stringContaining('/workouts/list'));
  });

  it('should handle delete workout', async () => {
    const initialWorkouts: WorkoutLog[] = [
      { id: '1', date: '2024-01-01', workout_type: 'Legs', exercises: [] } as unknown as WorkoutLog,
      { id: '2', date: '2024-01-02', workout_type: 'Upper', exercises: [] } as unknown as WorkoutLog,
    ];
    
    // Manually set state for test
    useWorkoutStore.setState({ workouts: initialWorkouts, total: 2 });

    vi.mocked(httpClient).mockResolvedValue({ message: 'Deleted' });

    await useWorkoutStore.getState().deleteWorkout('1');

    const state = useWorkoutStore.getState();
    expect(state.workouts).toHaveLength(1);
    expect(state.workouts[0].id).toBe('2');
    expect(state.total).toBe(1);
    expect(httpClient).toHaveBeenCalledWith('/workouts/1', { method: 'DELETE' });
  });

  it('should handle fetch errors', async () => {
    vi.mocked(httpClient).mockRejectedValue(new Error('API Error'));

    await useWorkoutStore.getState().fetchWorkouts();

    const state = useWorkoutStore.getState();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBe('Falha ao carregar treinos. Tente novamente mais tarde.');
  });
});
