import { create } from 'zustand';

import { httpClient } from '../api/http-client';
import type {
  CreateWorkoutRequest,
  WorkoutLog,
  WorkoutListResponse,
} from '../types/workout';

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
  createWorkout: (data: CreateWorkoutRequest) => Promise<WorkoutLog>;
  deleteWorkout: (id: string) => Promise<void>;
  fetchWorkoutTypes: () => Promise<string[]>;
  fetchExerciseSuggestions: () => Promise<string[]>;
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
      const data =
        (await httpClient<WorkoutListResponse>(
          `/workout/list?page=${String(page)}&page_size=${String(limit)}`
        )) ?? {
          workouts: [],
          total: 0,
          page,
          page_size: limit,
          total_pages: 0,
        };
      set({
        workouts: data.workouts,
        total: data.total,
        page: data.page,
        totalPages: data.total_pages,
        isLoading: false,
      });
    } catch (err) {
      set({ 
        error: err instanceof Error ? err.message : 'Error fetching workouts', 
        isLoading: false 
      });
    }
  },

  createWorkout: async (data) => {
    const createdWorkout = await httpClient<WorkoutLog>('/workout', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    if (!createdWorkout) {
      throw new Error('Failed to create workout');
    }

    const { workouts, total } = get();
    set({
      workouts: [createdWorkout, ...workouts],
      total: total + 1,
    });
    return createdWorkout;
  },

  deleteWorkout: async (id: string) => {
    await httpClient(`/workout/${id}`, { method: 'DELETE' });
    const { workouts, total } = get();
    set({
      workouts: workouts.filter(w => w.id !== id),
      total: total - 1
    });
  },

  fetchWorkoutTypes: async () => {
    return (await httpClient<string[]>('/workout/types')) ?? [];
  },

  fetchExerciseSuggestions: async () => {
    return (await httpClient<string[]>('/workout/exercises')) ?? [];
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
