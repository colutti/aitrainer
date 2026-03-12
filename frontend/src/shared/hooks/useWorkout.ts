import { create } from 'zustand';

import { httpClient } from '../api/http-client';
import type { WorkoutListResponse, WorkoutLog } from '../types/workout';

interface WorkoutState {
  workouts: WorkoutLog[];
  total: number;
  page: number;
  totalPages: number;
  isLoading: boolean;
  error: string | null;
  selectedWorkout: WorkoutLog | null;
}

interface WorkoutActions {
  fetchWorkouts: (page?: number) => Promise<void>;
  deleteWorkout: (id: string) => Promise<void>;
  setSelectedWorkout: (workout: WorkoutLog | null) => void;
  reset: () => void;
}

type WorkoutStore = WorkoutState & WorkoutActions;

/**
 * Workout store using Zustand
 * 
 * Manages the global state for workout logs, including fetching, pagination, and deletion.
 */
export const useWorkoutStore = create<WorkoutStore>((set, get) => ({
  workouts: [],
  total: 0,
  page: 1,
  totalPages: 0,
  isLoading: false,
  error: null,
  selectedWorkout: null,

  fetchWorkouts: async (page = 1) => {
    set({ isLoading: true, error: null });
    try {
      const params = new URLSearchParams();
      params.append('page', page.toString());

      const response = await httpClient<WorkoutListResponse>(`/workout/list?${params.toString()}`);
      
      if (response) {
        set({
          workouts: response.workouts,
          total: response.total,
          page: response.page,
          totalPages: response.total_pages,
        });
      }
      set({ isLoading: false });
    } catch (error) {
      console.error('Error fetching workouts:', error);
      set({ 
        isLoading: false, 
        error: 'Falha ao carregar treinos. Tente novamente mais tarde.' 
      });
    }
  },

  deleteWorkout: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      await httpClient(`/workout/${id}`, { method: 'DELETE' });
      
      const { workouts, total } = get();
      set({
        workouts: workouts.filter((w) => w.id !== id),
        total: total - 1,
        isLoading: false,
      });
    } catch (error) {
      console.error('Error deleting workout:', error);
      set({ 
        isLoading: false, 
        error: 'Falha ao excluir treino. Tente novamente.' 
      });
      throw error;
    }
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
