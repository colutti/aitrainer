import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { useConfirmation } from '../../shared/hooks/useConfirmation';
import { useWorkoutStore } from '../../shared/hooks/useWorkout';

import WorkoutsPage from './WorkoutsPage';

// Mocks
vi.mock('../../shared/hooks/useWorkout', () => ({
  useWorkoutStore: vi.fn(),
}));

vi.mock('../../shared/hooks/useConfirmation', () => ({
  useConfirmation: vi.fn(),
}));

describe('WorkoutsPage', () => {
  const mockFetchWorkouts = vi.fn();
  const mockDeleteWorkout = vi.fn();
  const mockSetSelectedWorkout = vi.fn();

  const defaultHookValues = {
    workouts: [
      { 
        id: 'w1', 
        date: '2024-01-01', 
        workout_type: 'Strength', 
        exercises: [{ 
          name: 'Deadlift', 
          sets: 1, 
          reps_per_set: [5], 
          weights_per_set: [100] 
        }],
        duration_minutes: 45,
        source: 'manual'
      }
    ],
    isLoading: false,
    fetchWorkouts: mockFetchWorkouts,
    deleteWorkout: mockDeleteWorkout,
    totalPages: 2,
    page: 1,
    selectedWorkout: null,
    setSelectedWorkout: mockSetSelectedWorkout,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useWorkoutStore).mockReturnValue(defaultHookValues as any);
    vi.mocked(useConfirmation).mockReturnValue({ confirm: vi.fn().mockResolvedValue(true) } as any);
  });

  it('should render workouts and call fetch on mount', () => {
    render(<WorkoutsPage />);
    expect(mockFetchWorkouts).toHaveBeenCalled();
    expect(screen.getByText('Strength')).toBeInTheDocument();
  });

  it('should handle deletion success', async () => {
    const mockDelete = vi.fn().mockResolvedValue({});
    vi.mocked(useWorkoutStore).mockReturnValue({
      ...defaultHookValues,
      deleteWorkout: mockDelete,
    } as any);

    render(<WorkoutsPage />);
    
    const deleteBtn = screen.getAllByLabelText('Delete')[0]!;
    fireEvent.click(deleteBtn);
    
    await waitFor(() => {
      expect(mockDelete).toHaveBeenCalledWith('w1');
    });
  });
});
