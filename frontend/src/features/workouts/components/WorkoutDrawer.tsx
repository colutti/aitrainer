import { zodResolver } from '@hookform/resolvers/zod';
import { Activity, Clock3, Copy, Dumbbell, Plus, Save, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useFieldArray, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { z } from 'zod';

import { Button } from '../../../shared/components/ui/Button';
import { Input } from '../../../shared/components/ui/Input';
import { FormField } from '../../../shared/components/ui/premium/FormField';
import { PremiumDrawer } from '../../../shared/components/ui/premium/PremiumDrawer';
import { useWorkoutStore } from '../../../shared/hooks/useWorkout';
import type { CreateWorkoutRequest, Workout } from '../../../shared/types/workout';

const setSchema = z.object({
  reps: z.coerce.number().min(0),
  weight_kg: z.coerce.number().min(0),
  duration_seconds: z.preprocess(
    value => (value === '' || value === undefined ? undefined : Number(value)),
    z.number().min(0).optional()
  ),
  distance_meters: z.preprocess(
    value => (value === '' || value === undefined ? undefined : Number(value)),
    z.number().min(0).optional()
  ),
});

const exerciseSchema = z.object({
  exercise_title: z.string().min(2, 'Nome do exercício obrigatório'),
  sets: z.array(setSchema).min(1),
});

const workoutSchema = z.object({
  workout_type: z.string().min(2, 'Tipo de treino obrigatório'),
  duration_minutes: z.coerce.number().min(1).optional(),
  date: z.string().min(1),
  exercises: z.array(exerciseSchema).min(1, 'Adicione pelo menos um exercício'),
});

type WorkoutFormData = z.infer<typeof workoutSchema>;

interface WorkoutDrawerProps {
  workout?: Workout | null;
  isOpen: boolean;
  onClose: () => void;
}

const emptySet = {
  reps: 10,
  weight_kg: 0,
  duration_seconds: undefined,
  distance_meters: undefined,
};

const emptyExercise = {
  exercise_title: '',
  sets: [emptySet],
};

function collectOptionalSetMetric(
  sets: WorkoutFormData['exercises'][number]['sets'],
  key: 'duration_seconds' | 'distance_meters'
): number[] {
  return sets
    .map(set => set[key])
    .filter((value): value is number => value !== undefined);
}

function exerciseSetFieldId(
  exerciseIndex: number,
  setIndex: number,
  metric: 'weight' | 'reps' | 'duration' | 'distance'
): string {
  return `exercise-${String(exerciseIndex)}-set-${String(setIndex)}-${metric}`;
}

function exerciseSetsPath(exerciseIndex: number) {
  // eslint-disable-next-line @typescript-eslint/restrict-template-expressions
  return `exercises.${exerciseIndex}.sets` as const;
}

function exerciseTitlePath(exerciseIndex: number) {
  // eslint-disable-next-line @typescript-eslint/restrict-template-expressions
  return `exercises.${exerciseIndex}.exercise_title` as const;
}

export function WorkoutDrawer({ workout, isOpen, onClose }: WorkoutDrawerProps) {
  const { t } = useTranslation();
  const { createWorkout, fetchWorkoutTypes, fetchExerciseSuggestions } = useWorkoutStore();
  const [workoutTypeSuggestions, setWorkoutTypeSuggestions] = useState<string[]>([]);
  const [exerciseSuggestions, setExerciseSuggestions] = useState<string[]>([]);

  const {
    register,
    control,
    handleSubmit,
    getValues,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<WorkoutFormData>({
    resolver: zodResolver(workoutSchema),
    defaultValues: {
      workout_type: '',
      duration_minutes: 60,
      date: new Date().toISOString().split('T')[0],
      exercises: [],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'exercises',
  });

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const loadSuggestions = async () => {
      const [types, exercises] = await Promise.all([
        fetchWorkoutTypes(),
        fetchExerciseSuggestions(),
      ]);
      setWorkoutTypeSuggestions(types);
      setExerciseSuggestions(exercises);
    };

    void loadSuggestions();
  }, [fetchExerciseSuggestions, fetchWorkoutTypes, isOpen]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    if (workout) {
      reset({
        workout_type: workout.workout_type ?? '',
        duration_minutes: workout.duration_minutes ?? 60,
        date: workout.date.split('T')[0] ?? new Date().toISOString().split('T')[0],
        exercises: workout.exercises.map(exercise => ({
          exercise_title: exercise.exercise_title,
          sets: exercise.sets.map(set => ({
            reps: set.reps ?? 0,
            weight_kg: set.weight_kg ?? 0,
            duration_seconds: set.duration_seconds,
            distance_meters: set.distance_meters,
          })),
        })),
      });
      return;
    }

    reset({
      workout_type: '',
      duration_minutes: 60,
      date: new Date().toISOString().split('T')[0],
      exercises: [],
    });
  }, [isOpen, reset, workout]);

  const onSubmit = async (data: WorkoutFormData) => {
    const payload: CreateWorkoutRequest = {
      date: data.date,
      workout_type: data.workout_type,
      duration_minutes: data.duration_minutes,
      source: 'manual',
      exercises: data.exercises.map(exercise => ({
        name: exercise.exercise_title,
        sets: exercise.sets.length,
        reps_per_set: exercise.sets.map(set => set.reps),
        weights_per_set: exercise.sets.map(set => set.weight_kg),
        duration_seconds_per_set: collectOptionalSetMetric(exercise.sets, 'duration_seconds'),
        distance_meters_per_set: collectOptionalSetMetric(exercise.sets, 'distance_meters'),
      })),
    };

    await createWorkout(payload);
    onClose();
  };

  return (
    <PremiumDrawer
      isOpen={isOpen}
      onClose={onClose}
      title={workout ? t('workouts.edit_workout') : t('workouts.register_workout')}
      subtitle={workout ? workout.date.split('T')[0] : t('workouts.subtitle')}
      icon={<Dumbbell size={24} />}
    >
      <form onSubmit={(event) => { void handleSubmit(onSubmit)(event); }} className="space-y-8 pb-24">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FormField
            label={t('workouts.workout_type')}
            id="workout-type"
            icon={<Activity size={14} />}
            error={errors.workout_type?.message}
          >
            <Input
              id="workout-type"
              list="workout-type-suggestions"
              {...register('workout_type')}
              className="h-14 bg-white/5 border-white/5 rounded-2xl font-bold"
            />
          </FormField>

          <FormField
            label={t('workouts.duration')}
            id="workout-duration"
            icon={<Clock3 size={14} />}
            error={errors.duration_minutes?.message}
          >
            <Input
              id="workout-duration"
              type="number"
              {...register('duration_minutes')}
              className="h-14 bg-white/5 border-white/5 rounded-2xl font-bold"
            />
          </FormField>
        </div>

        <datalist id="workout-type-suggestions">
          {workoutTypeSuggestions.map(option => (
            <option key={option} value={option} />
          ))}
        </datalist>

        <div className="space-y-6">
          <div className="flex items-center justify-between pb-2 border-b border-white/5">
            <div className="flex items-center gap-2">
              <Dumbbell size={18} className="text-indigo-400" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                {t('workouts.exercises')}
              </h3>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => { append(emptyExercise); }}
            >
              <Plus size={14} />
              Adicionar exercício
            </Button>
          </div>

          {errors.exercises?.message && (
            <p className="text-sm text-red-400">{errors.exercises.message}</p>
          )}

          <div className="space-y-4">
            {fields.map((field, exerciseIndex) => (
              <ExerciseCard
                key={field.id}
                control={control}
                exerciseIndex={exerciseIndex}
                getValues={getValues}
                register={register}
                removeExercise={() => { remove(exerciseIndex); }}
                exerciseSuggestions={exerciseSuggestions}
              />
            ))}
          </div>
        </div>

        <div className="sticky bottom-0 pt-6 bg-[#0d0d0f]/95 backdrop-blur-sm border-t border-white/5 flex gap-4">
          <Button fullWidth variant="secondary" type="button" onClick={onClose}>
            {t('common.cancel')}
          </Button>
          <Button fullWidth type="submit" isLoading={isSubmitting} className="btn-premium">
            <Save size={18} />
            Salvar treino
          </Button>
        </div>
      </form>
    </PremiumDrawer>
  );
}

interface ExerciseCardProps {
  control: ReturnType<typeof useForm<WorkoutFormData>>['control'];
  exerciseIndex: number;
  getValues: ReturnType<typeof useForm<WorkoutFormData>>['getValues'];
  register: ReturnType<typeof useForm<WorkoutFormData>>['register'];
  removeExercise: () => void;
  exerciseSuggestions: string[];
}

function ExerciseCard({
  control,
  exerciseIndex,
  getValues,
  register,
  removeExercise,
  exerciseSuggestions,
}: ExerciseCardProps) {
  const setArray = useFieldArray({
    control,
    name: exerciseSetsPath(exerciseIndex),
  });

  return (
    <div className="p-6 rounded-3xl bg-white/5 border border-white/5 space-y-4">
      <div className="flex items-start gap-3">
        <FormField
          label="Nome do exercício"
          id={`exercise-${String(exerciseIndex)}`}
          className="flex-1"
        >
          <Input
            id={`exercise-${String(exerciseIndex)}`}
            list={`exercise-suggestions-${String(exerciseIndex)}`}
            placeholder="Nome do Exercício"
            {...register(exerciseTitlePath(exerciseIndex))}
            className="h-12 bg-transparent border-white/10 rounded-2xl font-bold"
          />
        </FormField>
        <Button type="button" variant="ghost" size="sm" onClick={removeExercise}>
          <Trash2 size={16} />
        </Button>
      </div>

      <datalist id={`exercise-suggestions-${String(exerciseIndex)}`}>
        {exerciseSuggestions.map(option => (
          <option key={option} value={option} />
        ))}
      </datalist>

      <div className="space-y-3">
        {setArray.fields.map((setField, setIndex) => (
          <div key={setField.id} className="rounded-2xl border border-white/5 bg-black/20 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-black uppercase tracking-widest text-zinc-400">
                Série {setIndex + 1}
              </span>
              {setArray.fields.length > 1 && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => { setArray.remove(setIndex); }}
                >
                  <Trash2 size={14} />
                </Button>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Input
                id={exerciseSetFieldId(exerciseIndex, setIndex, 'weight')}
                type="number"
                label="Peso"
                // eslint-disable-next-line @typescript-eslint/restrict-template-expressions
                {...register(`exercises.${exerciseIndex}.sets.${setIndex}.weight_kg` as const)}
              />
              <Input
                id={exerciseSetFieldId(exerciseIndex, setIndex, 'reps')}
                type="number"
                label="Reps"
                // eslint-disable-next-line @typescript-eslint/restrict-template-expressions
                {...register(`exercises.${exerciseIndex}.sets.${setIndex}.reps` as const)}
              />
              <Input
                id={exerciseSetFieldId(exerciseIndex, setIndex, 'duration')}
                type="number"
                label="Tempo"
                // eslint-disable-next-line @typescript-eslint/restrict-template-expressions
                {...register(`exercises.${exerciseIndex}.sets.${setIndex}.duration_seconds` as const)}
              />
              <Input
                id={exerciseSetFieldId(exerciseIndex, setIndex, 'distance')}
                type="number"
                label="Distância"
                // eslint-disable-next-line @typescript-eslint/restrict-template-expressions
                {...register(`exercises.${exerciseIndex}.sets.${setIndex}.distance_meters` as const)}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-3">
        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={() => { setArray.append(emptySet); }}
        >
          <Plus size={14} />
          Adicionar série
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => {
            const exerciseSets = getValues('exercises')[exerciseIndex]?.sets ?? [];
            const lastSet = exerciseSets.at(-1);
            setArray.append({
              reps: lastSet?.reps ?? 0,
              weight_kg: lastSet?.weight_kg ?? 0,
              duration_seconds: lastSet?.duration_seconds,
              distance_meters: lastSet?.distance_meters,
            });
          }}
        >
          <Copy size={14} />
          Duplicar última série
        </Button>
      </div>
    </div>
  );
}
