import { describe, it, expect, vi, beforeEach } from 'vitest';

import { act, render, screen, fireEvent, waitFor } from '../../../shared/utils/test-utils';

import { WorkoutDrawer } from './WorkoutDrawer';

const mockCreateWorkout = vi.fn();
const mockUpdateWorkout = vi.fn();
const mockFetchWorkoutTypes = vi.fn();
const mockFetchExerciseSuggestions = vi.fn();

function getSetMetricInput(
  exerciseIndex: number,
  setIndex: number,
  metric: 'weight' | 'reps' | 'duration' | 'distance'
) {
  return document.getElementById(
    `exercise-${String(exerciseIndex)}-set-${String(setIndex)}-${metric}`
  ) as HTMLInputElement;
}

vi.mock('../../../shared/hooks/useWorkout', () => ({
  useWorkoutStore: () => ({
    createWorkout: mockCreateWorkout,
    updateWorkout: mockUpdateWorkout,
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
    expect(screen.queryByText(/Gerencie seu histórico de performance/i)).not.toBeInTheDocument();

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
      external_id: undefined,
      notes: undefined,
    });

    render(<WorkoutDrawer {...defaultProps} />);

    fireEvent.change(screen.getByLabelText(/Tipo de Treino/i), {
      target: { value: 'Push' },
    });
    fireEvent.change(screen.getByLabelText(/Data/i), {
      target: { value: '2026-04-02' },
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
        date: '2026-04-02',
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

  it('submits all supported per-set workout metrics on create', async () => {
    mockCreateWorkout.mockResolvedValue({
      id: 'workout-extended',
      user_email: 'test@test.com',
      date: '2026-04-03',
      workout_type: 'Hybrid',
      duration_minutes: 70,
      exercises: [],
      source: 'manual',
      external_id: undefined,
      notes: undefined,
    });

    render(<WorkoutDrawer {...defaultProps} />);

    fireEvent.change(screen.getByLabelText(/Tipo de Treino/i), {
      target: { value: 'Hybrid' },
    });
    fireEvent.change(screen.getByLabelText(/Data/i), {
      target: { value: '2026-04-03' },
    });
    fireEvent.change(screen.getByLabelText(/Duração/i), {
      target: { value: '70' },
    });

    fireEvent.click(screen.getByRole('button', { name: /Adicionar exercício/i }));
    fireEvent.change(screen.getByLabelText(/Nome do exercício/i), {
      target: { value: 'Row Erg' },
    });

    const addSetButton = screen.getByRole('button', { name: /Adicionar série/i });
    fireEvent.click(addSetButton);

    fireEvent.change(getSetMetricInput(0, 0, 'weight'), { target: { value: '50' } });
    fireEvent.change(getSetMetricInput(0, 0, 'reps'), { target: { value: '12' } });
    fireEvent.change(getSetMetricInput(0, 0, 'duration'), { target: { value: '90' } });
    fireEvent.change(getSetMetricInput(0, 0, 'distance'), { target: { value: '400' } });

    fireEvent.change(getSetMetricInput(0, 1, 'weight'), { target: { value: '55' } });
    fireEvent.change(getSetMetricInput(0, 1, 'reps'), { target: { value: '10' } });
    fireEvent.change(getSetMetricInput(0, 1, 'duration'), { target: { value: '95' } });
    fireEvent.change(getSetMetricInput(0, 1, 'distance'), { target: { value: '450' } });

    fireEvent.click(screen.getByRole('button', { name: /Salvar treino/i }));

    await waitFor(() => {
      expect(mockCreateWorkout).toHaveBeenCalledWith({
        date: '2026-04-03',
        workout_type: 'Hybrid',
        duration_minutes: 70,
        source: 'manual',
        exercises: [
          {
            name: 'Row Erg',
            sets: 2,
            reps_per_set: [12, 10],
            weights_per_set: [50, 55],
            duration_seconds_per_set: [90, 95],
            distance_meters_per_set: [400, 450],
          },
        ],
      });
    });
  });

  it('updates an existing workout with all supported per-set workout metrics', async () => {
    mockUpdateWorkout.mockResolvedValue({
      id: 'workout-2',
      user_email: 'test@test.com',
      date: '2026-04-15',
      workout_type: 'Pull',
      duration_minutes: 52,
      exercises: [],
      source: 'manual',
      external_id: undefined,
      notes: undefined,
    });
    const existingWorkout = {
      id: 'workout-2',
      date: '2026-04-15T10:00:00Z',
      workout_type: 'Pull',
      duration_minutes: 50,
      exercises: [
        {
          exercise_title: 'Barbell Row',
          sets: [{ set_index: 1, reps: 8, weight_kg: 80, duration_seconds: 60, distance_meters: 0 }],
        },
      ],
      notes: undefined,
      source: 'manual',
      external_id: undefined,
      user_email: 'test@test.com',
    };

    render(<WorkoutDrawer {...defaultProps} workout={existingWorkout} />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Data/i)).toHaveValue('2026-04-15');
    });

    fireEvent.change(screen.getByLabelText(/Tipo de Treino/i), {
      target: { value: 'Pull Strength' },
    });
    fireEvent.change(screen.getByLabelText(/Duração/i), {
      target: { value: '52' },
    });
    fireEvent.change(screen.getByLabelText(/Nome do exercício/i), {
      target: { value: 'Barbell Row Updated' },
    });

    fireEvent.change(getSetMetricInput(0, 0, 'weight'), { target: { value: '82.5' } });
    fireEvent.change(getSetMetricInput(0, 0, 'reps'), { target: { value: '9' } });
    fireEvent.change(getSetMetricInput(0, 0, 'duration'), { target: { value: '75' } });
    fireEvent.change(getSetMetricInput(0, 0, 'distance'), { target: { value: '25' } });

    fireEvent.click(screen.getByRole('button', { name: /Duplicar última série/i }));

    fireEvent.change(getSetMetricInput(0, 1, 'weight'), { target: { value: '85' } });
    fireEvent.change(getSetMetricInput(0, 1, 'reps'), { target: { value: '7' } });
    fireEvent.change(getSetMetricInput(0, 1, 'duration'), { target: { value: '80' } });
    fireEvent.change(getSetMetricInput(0, 1, 'distance'), { target: { value: '30' } });

    fireEvent.click(screen.getByRole('button', { name: /Salvar treino/i }));

    await waitFor(() => {
      expect(mockUpdateWorkout).toHaveBeenCalledWith('workout-2', {
        date: '2026-04-15',
        workout_type: 'Pull Strength',
        duration_minutes: 52,
        source: 'manual',
        exercises: [
          {
            name: 'Barbell Row Updated',
            sets: 2,
            reps_per_set: [9, 7],
            weights_per_set: [82.5, 85],
            duration_seconds_per_set: [75, 80],
            distance_meters_per_set: [25, 30],
          },
        ],
      });
      expect(defaultProps.onClose).toHaveBeenCalled();
    });
  });

  it('preloads date when editing an existing workout', async () => {
    const existingWorkout = {
      id: 'workout-2',
      date: '2026-04-15T10:00:00Z',
      workout_type: 'Pull',
      duration_minutes: 50,
      exercises: [
        {
          exercise_title: 'Barbell Row',
          sets: [{ set_index: 1, reps: 8, weight_kg: 80 }],
        },
      ],
      notes: undefined,
      source: 'manual',
      external_id: undefined,
      user_email: 'test@test.com',
    };

    render(<WorkoutDrawer {...defaultProps} workout={existingWorkout} />);

    await waitFor(() => {
      expect(screen.getByLabelText(/Data/i)).toHaveValue('2026-04-15');
    });
  });

  it('disables form controls in read-only mode', async () => {
    act(() => {
      render(<WorkoutDrawer {...defaultProps} isReadOnly />);
    });

    await waitFor(() => {
      expect(mockFetchWorkoutTypes).toHaveBeenCalled();
      expect(mockFetchExerciseSuggestions).toHaveBeenCalled();
    });

    expect(screen.getByText(/Demo Read-Only/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Tipo de Treino/i)).toBeDisabled();
    expect(screen.getByRole('button', { name: /Salvar treino/i })).toBeDisabled();
    expect(screen.queryByRole('button', { name: /Adicionar exercício/i })).toBeDisabled();
  });

  it('renders action footer without solid dark block background', async () => {
    const { container } = render(<WorkoutDrawer {...defaultProps} />);

    await waitFor(() => {
      expect(mockFetchWorkoutTypes).toHaveBeenCalled();
      expect(mockFetchExerciseSuggestions).toHaveBeenCalled();
    });

    const cancelButton = screen.getByRole('button', { name: /Cancelar/i });
    const footer = cancelButton.closest('div');

    expect(footer).toBeTruthy();
    expect(footer?.className).not.toContain('bg-[#0d0d0f]/95');
    expect(container.querySelector('.from-\\[\\#0d0d0f\\]\\/80')).toBeTruthy();
  });
});
