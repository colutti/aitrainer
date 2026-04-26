import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { WorkoutCard } from './WorkoutCard';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'workouts.general_training': 'Treino geral',
        'workouts.synced_label': 'Sincronizado',
        'workouts.total_volume': 'Volume total',
        'workouts.unit_ton': 't',
        'workouts.unit_kg': 'kg',
        'workouts.delete_confirm_btn': 'Excluir',
        'workouts.exercises': 'Exercícios',
        'shared.edit': 'Editar',
      };
      return translations[key] ?? key;
    },
  }),
}));

const mockWorkout = {
  id: '1',
  user_email: 'test@test.com',
  date: '2024-01-01T10:00:00Z',
  workout_type: 'Leg Day',
  duration_minutes: 60,
  source: 'manual',
  external_id: null,
  notes: '',
  exercises: [
    {
      exercise_id: 'ex1',
      exercise_title: 'Squat',
      sets: [
        { set_index: 1, reps: 10, weight_kg: 100 },
        { set_index: 2, reps: 10, weight_kg: 100 }
      ]
    }
  ]
} as any;

describe('WorkoutCard', () => {
  it('should render workout details', () => {
    render(<WorkoutCard workout={mockWorkout} />);
    
    expect(screen.getByText(/Leg Day/i)).toBeInTheDocument();
    // Check volume (2000kg = 2.0t)
    expect(screen.getByText(/2\.0/)).toBeInTheDocument(); 
    expect(screen.getAllByText(/t/i).length).toBeGreaterThan(0);
    // Check duration with flexible regex
    expect(screen.getByText(/60/)).toBeInTheDocument();
  });

  it('should show "Sincronizado" tag when source is hevy', () => {
    render(<WorkoutCard workout={{ ...mockWorkout, source: 'hevy', workout_type: undefined }} />);
    expect(screen.getByText(/Sincronizado/i)).toBeInTheDocument();
  });

  it('should call onDelete when delete button is clicked', () => {
    const onDelete = vi.fn();
    render(<WorkoutCard workout={mockWorkout} onDelete={onDelete} />);
    
    const deleteBtn = screen.getByLabelText(/Excluir/i);
    fireEvent.click(deleteBtn);
    
    expect(onDelete).toHaveBeenCalledWith('1');
  });

  it('should call onClick when card is clicked', () => {
    const onClick = vi.fn();
    render(<WorkoutCard workout={mockWorkout} onClick={onClick} />);
    
    fireEvent.click(screen.getByTestId('workout-card'));
    expect(onClick).toHaveBeenCalledWith(mockWorkout);
  });

  it('should call onEdit when edit button is clicked', () => {
    const onEdit = vi.fn();
    render(<WorkoutCard workout={mockWorkout} onEdit={onEdit} />);

    const editBtn = screen.getByLabelText(/Editar/i);
    fireEvent.click(editBtn);

    expect(onEdit).toHaveBeenCalledWith(mockWorkout);
  });

  it('should keep delete action visible and accessible', () => {
    render(<WorkoutCard workout={mockWorkout} onDelete={vi.fn()} />);

    expect(screen.getByLabelText(/Excluir/i)).toBeInTheDocument();
  });
});
