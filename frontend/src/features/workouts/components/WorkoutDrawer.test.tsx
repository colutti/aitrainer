import { describe, it, expect, vi, beforeEach } from 'vitest';

import { act, render, screen, fireEvent, waitFor } from '../../../shared/utils/test-utils';

import { WorkoutDrawer } from './WorkoutDrawer';

const mockCreateWorkout = vi.fn();
const mockFetchWorkoutTypes = vi.fn();
const mockFetchExerciseSuggestions = vi.fn();

vi.mock('../../../shared/hooks/useWorkout', () => ({
  useWorkoutStore: () => ({
    createWorkout: mockCreateWorkout,
    fetchWorkoutTypes: mockFetchWorkoutTypes,
    fetchExerciseSuggestions: mockFetchExerciseSuggestions,
  }),
}));

describe('WorkoutDrawer', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    workout: null,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchWorkoutTypes.mockResolvedValue(['Push', 'Pull']);
    mockFetchExerciseSuggestions.mockResolvedValue(['Bench Press', 'Squat']);
  });

  it('renders register workout title and loads suggestions on open', async () => {
    render(<WorkoutDrawer {...defaultProps} />);

    expect(screen.getByText(/Registrar Treino/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(mockFetchWorkoutTypes).toHaveBeenCalled();
      expect(mockFetchExerciseSuggestions).toHaveBeenCalled();
    });
  });

  it('adds and duplicates a set within an exercise card', async () => {
    render(<WorkoutDrawer {...defaultProps} />);

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Adicionar exercício/i }));
    });
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Adicionar série/i }));
    });

    expect(screen.getAllByLabelText(/Peso/i)).toHaveLength(2);

    fireEvent.change(screen.getAllByLabelText(/Peso/i)[1]!, { target: { value: '60' } });
    fireEvent.change(screen.getAllByLabelText(/Reps/i)[1]!, { target: { value: '10' } });

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Duplicar última série/i }));
    });

    const weightInputs = screen.getAllByLabelText(/Peso/i);
    const repsInputs = screen.getAllByLabelText(/Reps/i);
    const duplicatedWeightInput = weightInputs[2] as HTMLInputElement | undefined;
    const duplicatedRepsInput = repsInputs[2] as HTMLInputElement | undefined;

    expect(duplicatedWeightInput?.value).toBe('60');
    expect(duplicatedRepsInput?.value).toBe('10');
  });

  it('renders exercise suggestions in the datalist', async () => {
    const { container } = render(<WorkoutDrawer {...defaultProps} />);

    fireEvent.click(screen.getByRole('button', { name: /Adicionar exercício/i }));

    await waitFor(() => {
      expect(container.querySelector('option[value="Bench Press"]')).toBeTruthy();
      expect(container.querySelector('option[value="Squat"]')).toBeTruthy();
    });

    expect(screen.getByPlaceholderText(/Nome do Exercício/i)).toBeInTheDocument();
  });

  it('submits a manual workout payload and closes on success', async () => {
    mockCreateWorkout.mockResolvedValue({
      id: 'workout-1',
      user_email: 'test@test.com',
      date: '2024-01-01',
      workout_type: 'Push',
      duration_minutes: 45,
      exercises: [],
      source: 'manual',
      external_id: null,
      notes: null,
    });

    render(<WorkoutDrawer {...defaultProps} />);

    fireEvent.change(screen.getByLabelText(/Tipo de Treino/i), {
      target: { value: 'Push' },
    });
    fireEvent.change(screen.getByLabelText(/Duração/i), {
      target: { value: '45' },
    });

    fireEvent.click(screen.getByRole('button', { name: /Adicionar exercício/i }));
    fireEvent.change(screen.getByLabelText(/Nome do exercício/i), {
      target: { value: 'Bench Press' },
    });
    fireEvent.change(screen.getByLabelText(/Peso/i), { target: { value: '60' } });
    fireEvent.change(screen.getByLabelText(/Reps/i), { target: { value: '10' } });

    fireEvent.click(screen.getByRole('button', { name: /Salvar treino/i }));

    await waitFor(() => {
      expect(mockCreateWorkout).toHaveBeenCalledWith({
        date: expect.stringMatching(/^\d{4}-\d{2}-\d{2}$/),
        workout_type: 'Push',
        duration_minutes: 45,
        source: 'manual',
        exercises: [
          {
            name: 'Bench Press',
            sets: 1,
            reps_per_set: [10],
            weights_per_set: [60],
            distance_meters_per_set: [],
            duration_seconds_per_set: [],
          },
        ],
      });
      expect(defaultProps.onClose).toHaveBeenCalled();
    });
  });

  it('disables form controls in read-only mode', () => {
    act(() => {
      render(<WorkoutDrawer {...defaultProps} isReadOnly />);
    });

    expect(screen.getByText(/Demo Read-Only/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Tipo de Treino/i)).toBeDisabled();
    expect(screen.getByRole('button', { name: /Salvar treino/i })).toBeDisabled();
    expect(screen.queryByRole('button', { name: /Adicionar exercício/i })).toBeDisabled();
  });
});
