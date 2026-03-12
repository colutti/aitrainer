import { httpClient } from '../../../shared/api/http-client';
import type { WorkoutLog, WorkoutListResponse } from '../../../shared/types/workout';

/**
 * API client for Workout endpoints
 */
export const workoutsApi = {
  /**
   * Fetch paginated list of workouts
   * @param page - Page number (1-indexed)
   * @param pageSize - Number of workouts per page
   * @returns Paginated workout list
   */
  getWorkouts: async (page = 1, pageSize = 10): Promise<WorkoutListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    
    const result = await httpClient<WorkoutListResponse>(`/workout/list?${params.toString()}`);
    return result ?? {
      workouts: [],
      total: 0,
      page: 1,
      page_size: 10,
      total_pages: 0
    };
  },

  /**
   * Get workout details by ID
   * @param id - Workout ID
   * @returns Workout details with exercises
   */
  getWorkoutById: async (id: string): Promise<WorkoutLog> => {
    return httpClient<WorkoutLog>(`/workout/${id}`) as Promise<WorkoutLog>;
  },

  /**
   * Delete a workout by ID
   * @param id - Workout ID
   */
  deleteWorkout: async (id: string): Promise<void> => {
    await httpClient(`/workout/${id}`, { method: 'DELETE' });
  },
};
