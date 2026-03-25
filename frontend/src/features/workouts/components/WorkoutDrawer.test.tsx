import { describe, it, expect, vi } from 'vitest';

import { render, screen, fireEvent, waitFor } from '../../../shared/utils/test-utils';

import { WorkoutDrawer } from './WorkoutDrawer';

// Mocks
vi.mock('../../../shared/hooks/useWorkout', () => ({
  useWorkoutStore: () => ({
    fetchWorkouts: vi.fn(),
  }),
}));

describe('WorkoutDrawer', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    workout: null,
  };

  it('should render register workout title when no workout provided', () => {
    render(<WorkoutDrawer {...defaultProps} />);
    expect(screen.getByText(/Registrar Treino/i)).toBeInTheDocument();
  });

  it('should render edit workout title when workout provided', () => {
    const mockWorkout = {
      id: '1',
      date: '2024-01-01',
      workout_type: 'Strength',
      duration_minutes: 45,
      exercises: [
        {
          exercise_title: 'Bench Press',
          sets: [{ set_index: 0, reps: 10, weight_kg: 60 }],
        }
      ],
    };
    render(<WorkoutDrawer {...defaultProps} workout={mockWorkout as any} />);
    expect(screen.getByText(/Editar Treino/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue('Strength')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Bench Press')).toBeInTheDocument();
  });

  it('should add a new exercise field when "Adicionar" is clicked', async () => {
    render(<WorkoutDrawer {...defaultProps} />);
    
    const addBtn = screen.getByText(/Adicionar/i);
    fireEvent.click(addBtn);
    
    expect(screen.getByPlaceholderText(/Nome do Exercício/i)).toBeInTheDocument();
  });

  it('should handle form submission', async () => {
    render(<WorkoutDrawer {...defaultProps} />);
    
    const typeInput = screen.getByLabelText(/Tipo de Treino/i);
    fireEvent.change(typeInput, { target: { value: 'Cardio' } });
    
    // Add exercise to pass validation
    fireEvent.click(screen.getByText(/Adicionar/i));
    const exerciseInput = screen.getByPlaceholderText(/Nome do Exercício/i);
    fireEvent.change(exerciseInput, { target: { value: 'Running' } });

    const saveBtn = screen.getByText(/Salvar/i);
    fireEvent.click(saveBtn);
    
    await waitFor(() => {
      expect(defaultProps.onClose).toHaveBeenCalled();
    });
  });
});
