import { create } from 'zustand';

import { httpClient } from '../api/http-client';
import type { WorkoutLog, WorkoutListResponse } from '../types/workout';

interface WorkoutState {
  workouts: WorkoutLog[];
  total: number;
  page: number;
  totalPages: number;
  isLoading: boolean;
  error: string | null;
  selectedWorkout: WorkoutLog | null;
  
  // Actions
  fetchWorkouts: (page?: number, limit?: number) => Promise<void>;
  deleteWorkout: (id: string) => Promise<void>;
  setSelectedWorkout: (workout: WorkoutLog | null) => void;
  reset: () => void;
}

/**
 * Standardized Workout Store.
 */
export const useWorkoutStore = create<WorkoutState>((set, get) => ({
  workouts: [],
  total: 0,
  page: 1,
  totalPages: 0,
  isLoading: false,
  error: null,
  selectedWorkout: null,

  fetchWorkouts: async (page = 1, limit = 20) => {
    set({ isLoading: true, error: null });
    try {
      const data = await httpClient<WorkoutListResponse>(`/workouts?page=${String(page)}&limit=${String(limit)}`);
      if (data) {
        set({
          workouts: data.workouts,
          total: data.total,
          page: data.page,
          totalPages: data.total_pages,
          isLoading: false
        });
      } else {
        set({ isLoading: false });
      }
    } catch (err) {
      set({ 
        error: err instanceof Error ? err.message : 'Error fetching workouts', 
        isLoading: false 
      });
    }
  },

  deleteWorkout: async (id: string) => {
    await httpClient(`/workouts/${id}`, { method: 'DELETE' });
    const { workouts, total } = get();
    set({
      workouts: workouts.filter(w => w.id !== id),
      total: total - 1
    });
  },

  setSelectedWorkout: (workout) => {
    set({ selectedWorkout: workout });
  },

  reset: () => {
    set({
      workouts: [],
      total: 0,
      page: 1,
      totalPages: 0,
      isLoading: false,
      error: null,
      selectedWorkout: null,
    });
  },
}));
