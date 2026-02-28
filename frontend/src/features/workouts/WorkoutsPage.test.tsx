import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { useConfirmation } from '../../shared/hooks/useConfirmation';
import { useNotificationStore } from '../../shared/hooks/useNotification';
import { useWorkoutStore } from '../../shared/hooks/useWorkout';

import { WorkoutsPage } from './WorkoutsPage';

vi.mock('../../shared/hooks/useWorkout', () => ({
  useWorkoutStore: vi.fn(),
}));

vi.mock('../../shared/hooks/useNotification', () => ({
  useNotificationStore: vi.fn(),
}));

vi.mock('../../shared/hooks/useConfirmation', () => ({
  useConfirmation: vi.fn(),
}));

// Mock child components
vi.mock('./components/WorkoutCard', () => ({
  WorkoutCard: ({ workout, onDelete, onClick }: any) => (
    <div data-testid="workout-card" onClick={onClick}>
      <span>{workout.workout_type}</span>
      <button onClick={(e) => { e.stopPropagation(); onDelete(workout.id); }}>Delete</button>
    </div>
  )
}));

vi.mock('./components/WorkoutDrawer', () => ({
  WorkoutDrawer: ({ isOpen, onClose }: any) => (
    isOpen ? <div data-testid="workout-drawer"><button onClick={onClose}>Close</button></div> : null
  )
}));

vi.mock('../../shared/components/ui/DataList', () => ({
    DataList: ({ data, renderItem, keyExtractor, pagination, headerContent }: any) => (
        <div>
            {headerContent}
            {data.map((item: any) => (
                <div key={keyExtractor ? keyExtractor(item) : item.id}>
                    {renderItem(item)}
                </div>
            ))}
            {pagination && (
                <button onClick={() => pagination.onPageChange(pagination.currentPage + 1)}>
                    Next Page
                </button>
            )}
        </div>
    )
}));

describe('WorkoutsPage', () => {
  const mockFetchWorkouts = vi.fn();
  const mockDeleteWorkout = vi.fn();
  const mockSetSelectedWorkout = vi.fn();
  const mockNotify = { error: vi.fn(), success: vi.fn() };
  const mockConfirm = vi.fn();

  const mockWorkouts = [
    { 
      id: 'w1', 
      workout_type: 'Strength', 
      exercises: [{ name: 'Deadlift', reps_per_set: [5], weights_per_set: [100] }],
      date: '2024-01-01'
    }
  ];

  const mockStore = {
    workouts: mockWorkouts,
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
    (useWorkoutStore as any).mockReturnValue(mockStore);
    (useNotificationStore as any).mockReturnValue(mockNotify);
    (useConfirmation as any).mockReturnValue({ confirm: mockConfirm });
  });

  it('should handle search input', () => {
    render(<WorkoutsPage />);
    const input = screen.getByPlaceholderText(/Buscar por tipo ou exercício/i);
    fireEvent.change(input, { target: { value: 'test' } });
    expect(input).toHaveValue('test');
  });

  it('should handle deletion success', async () => {
    mockConfirm.mockResolvedValue(true);
    mockDeleteWorkout.mockResolvedValue(undefined);
    render(<WorkoutsPage />);
    
    fireEvent.click(screen.getAllByText('Delete')[0]!);
    await waitFor(() => {
      expect(mockDeleteWorkout).toHaveBeenCalledWith('w1');
    });
  });

  it('should handle pagination change', () => {
    render(<WorkoutsPage />);
    const nextBtn = screen.getByText('Next Page');
    fireEvent.click(nextBtn);
    expect(mockFetchWorkouts).toHaveBeenCalledWith(2);
  });
});
