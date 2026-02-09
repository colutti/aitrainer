import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { WorkoutDrawer } from './WorkoutDrawer';

const mockWorkout = {
  id: '1',
  date: '2024-01-15',
  duration_minutes: 45,
  notes: 'Great workout!',
  exercises: [
    {
      exercise_id: 'ex1',
      exercise_title: 'Bench Press',
      sets: [
        { set_index: 1, weight_kg: 80, reps: 8 },
        { set_index: 2, weight_kg: 82.5, reps: 6 },
      ],
      notes: 'Felt strong',
      pr_data: { weight: 82.5 }
    },
  ],
};

describe('WorkoutDrawer', () => {
  it('should not render when workout is null', () => {
    const { container } = render(
      <WorkoutDrawer workout={null} isOpen={true} onClose={() => { /* noop */ }} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('should render workout details when open', () => {
    render(
      <WorkoutDrawer workout={mockWorkout} isOpen={true} onClose={() => { /* noop */ }} />
    );

    expect(screen.getByText('Detalhes do Treino')).toBeInTheDocument();
    expect(screen.getByText('Bench Press')).toBeInTheDocument();
    expect(screen.getByText('2 séries')).toBeInTheDocument();
    expect(screen.getByText('Great workout!')).toBeInTheDocument();
  });

  it('should call onClose when backdrop is clicked', () => {
    const onClose = vi.fn();
    const { container } = render(
      <WorkoutDrawer workout={mockWorkout} isOpen={true} onClose={onClose} />
    );

    // The backdrop is the first child (first div in the fragment)
    const backdrop = container.firstChild as HTMLElement;
    fireEvent.click(backdrop);
    expect(onClose).toHaveBeenCalled();
  });

  it('should call onClose when X button is clicked', () => {
    const onClose = vi.fn();
    render(
      <WorkoutDrawer workout={mockWorkout} isOpen={true} onClose={onClose} />
    );

    const closeButton = screen.getByRole('button');
    fireEvent.click(closeButton);
    expect(onClose).toHaveBeenCalled();
  });

  it('should not be visible when isOpen is false', () => {
    const { container } = render(
      <WorkoutDrawer workout={mockWorkout} isOpen={false} onClose={() => { /* noop */ }} />
    );

    const drawer = container.querySelector('.translate-x-full');
    expect(drawer).toBeTruthy();
  });
});
