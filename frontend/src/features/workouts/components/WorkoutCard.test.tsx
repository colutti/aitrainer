import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { Workout } from '../../../shared/types/workout';

import { WorkoutCard } from './WorkoutCard';

describe('WorkoutCard', () => {
  const mockWorkout: Workout = {
    id: '1',
    date: '2024-01-01',
    workout_type: 'Leg Day',
    source: 'manual',
    duration_minutes: 60,
    exercises: [
      {
        exercise_title: 'Squat',
        sets: [
          { set_index: 1, reps: 10, weight_kg: 100 },
          { set_index: 2, reps: 10, weight_kg: 100 },
        ],
      },
    ],
  };

  it('should render workout details', () => {
    render(<WorkoutCard workout={mockWorkout} />);
    expect(screen.getByText('Leg Day')).toBeInTheDocument();
    // 2000kg is >= 1000, so it shows (2000/1000).toFixed(1) = 2.0
    expect(screen.getByText('2.0')).toBeInTheDocument(); 
    expect(screen.getByText('t')).toBeInTheDocument();
    expect(screen.getByText('60')).toBeInTheDocument();
  });

  it('should show "Hevy" tag when source is hevy', () => {
    render(<WorkoutCard workout={{ ...mockWorkout, source: 'hevy', workout_type: undefined }} />);
    expect(screen.getByText('Hevy')).toBeInTheDocument();
    expect(screen.getByText('Sincronizado')).toBeInTheDocument();
  });

  it('should call onDelete when delete button is clicked', () => {
    const onDelete = vi.fn();
    render(<WorkoutCard workout={mockWorkout} onDelete={onDelete} />);
    const deleteBtn = screen.getByTitle('Excluir treino');
    fireEvent.click(deleteBtn);
    expect(onDelete).toHaveBeenCalledWith('1');
  });

  it('should call onClick when card is clicked', () => {
    const onClick = vi.fn();
    render(<WorkoutCard workout={mockWorkout} onClick={onClick} />);
    fireEvent.click(screen.getByText('Leg Day'));
    expect(onClick).toHaveBeenCalledWith(mockWorkout);
  });

  it('should format large volume as tons', () => {
    const bigWorkout = {
      ...mockWorkout,
      exercises: [
        {
          exercise_title: 'Deadlift',
          sets: [{ set_index: 1, reps: 10, weight_kg: 1000 }], // 10,000 volume
        },
      ],
    };
    render(<WorkoutCard workout={bigWorkout} />);
    expect(screen.getByText('10.0')).toBeInTheDocument();
    expect(screen.getByText('t')).toBeInTheDocument();
  });
});
