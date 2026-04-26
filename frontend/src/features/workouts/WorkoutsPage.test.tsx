import { describe, it, expect, vi, beforeEach } from 'vitest';

import { useAuthStore } from '../../shared/hooks/useAuth';
import { useConfirmation } from '../../shared/hooks/useConfirmation';
import { useWorkoutStore } from '../../shared/hooks/useWorkout';
import { render, screen, fireEvent, waitFor } from '../../shared/utils/test-utils';

import WorkoutsPage from './WorkoutsPage';

// Mocks
vi.mock('../../shared/hooks/useWorkout', () => ({
  useWorkoutStore: vi.fn(),
}));

vi.mock('../../shared/hooks/useAuth', () => ({
  useAuthStore: vi.fn(),
}));

vi.mock('../../shared/hooks/useConfirmation', () => ({
  useConfirmation: vi.fn(),
}));

vi.mock('./components/WorkoutDrawer', () => ({
  WorkoutDrawer: ({ isOpen }: { isOpen: boolean }) => isOpen ? <div data-testid="workout-drawer" /> : null,
}));

describe('WorkoutsPage', () => {
  const mockFetchWorkouts = vi.fn();
  const mockDeleteWorkout = vi.fn();
  const mockFetchWorkoutTypes = vi.fn();
  const mockFetchExerciseSuggestions = vi.fn();
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
    fetchWorkoutTypes: mockFetchWorkoutTypes,
    fetchExerciseSuggestions: mockFetchExerciseSuggestions,
    totalPages: 2,
    page: 1,
    selectedWorkout: null,
    setSelectedWorkout: mockSetSelectedWorkout,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchWorkoutTypes.mockResolvedValue([]);
    mockFetchExerciseSuggestions.mockResolvedValue([]);
    vi.mocked(useWorkoutStore).mockReturnValue(defaultHookValues as any);
    vi.mocked(useConfirmation).mockReturnValue({ confirm: vi.fn().mockResolvedValue(true) } as any);
    vi.mocked(useAuthStore).mockReturnValue({ userInfo: { is_demo: false } } as any);
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
    
    const deleteBtn = screen.getAllByLabelText(/Excluir|Delete/i)[0]!;
    fireEvent.click(deleteBtn);
    
    await waitFor(() => {
      expect(mockDelete).toHaveBeenCalledWith('w1');
    });
  });

  it('should disable workout actions for demo users', () => {
    vi.mocked(useAuthStore).mockReturnValue({ userInfo: { is_demo: true } } as any);

    render(<WorkoutsPage />);

    expect(screen.getByRole('button', { name: /Registrar treino/i })).toBeDisabled();
    expect(screen.queryByTestId('btn-delete-workout')).not.toBeInTheDocument();
  });

  it('should allow viewing a workout card in demo mode', () => {
    vi.mocked(useAuthStore).mockReturnValue({ userInfo: { is_demo: true } } as any);

    render(<WorkoutsPage />);

    fireEvent.click(screen.getByTestId('workout-card'));

    expect(screen.getByTestId('workout-drawer')).toBeInTheDocument();
  });

  it('should open drawer automatically when action=log-workout is present in url', () => {
    render(<WorkoutsPage />, { route: '/dashboard/workouts?action=log-workout' });

    expect(screen.getByTestId('workout-drawer')).toBeInTheDocument();
  });

  it('should render pagination when workouts span multiple pages', () => {
    render(<WorkoutsPage />);

    expect(
      screen.getByText(
        (_content, element) => (
          element?.textContent === '1/2' &&
          element.className.includes('whitespace-nowrap')
        )
      )
    ).toBeInTheDocument();
    expect(screen.getAllByRole('button').length).toBeGreaterThan(3);
  });

  it('should fetch the next workout page when pagination advances', () => {
    render(<WorkoutsPage />);

    const buttons = screen.getAllByRole('button');
    const nextButton = buttons.at(buttons.length - 1);

    expect(nextButton).toBeTruthy();
    nextButton?.click();

    expect(mockFetchWorkouts).toHaveBeenCalledWith(2);
  });
});
