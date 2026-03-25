import { zodResolver } from '@hookform/resolvers/zod';
import { Dumbbell, Clock, Plus, Trash2, Save, Activity } from 'lucide-react';
import { useEffect } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { z } from 'zod';

import { Button } from '../../../shared/components/ui/Button';
import { Input } from '../../../shared/components/ui/Input';
import { FormField } from '../../../shared/components/ui/premium/FormField';
import { PremiumDrawer } from '../../../shared/components/ui/premium/PremiumDrawer';
import { useWorkoutStore } from '../../../shared/hooks/useWorkout';
import type { Workout } from '../../../shared/types/workout';

const exerciseSchema = z.object({
  exercise_title: z.string().min(2, 'Nome do exercício obrigatório'),
  sets: z.array(z.object({
    reps: z.number().min(1),
    weight_kg: z.number().min(0),
    set_index: z.number(),
  })).min(1),
});

const workoutSchema = z.object({
  workout_type: z.string().min(2, 'Tipo de treino obrigatório'),
  duration_minutes: z.number().min(1),
  date: z.string(),
  exercises: z.array(exerciseSchema),
});

type WorkoutFormData = z.infer<typeof workoutSchema>;

interface WorkoutDrawerProps {
  workout?: Workout | null;
  isOpen: boolean;
  onClose: () => void;
}

export function WorkoutDrawer({ workout, isOpen, onClose }: WorkoutDrawerProps) {
  const { t } = useTranslation();
  const { fetchWorkouts } = useWorkoutStore();
  
  const { register, control, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<WorkoutFormData>({
    resolver: zodResolver(workoutSchema),
    defaultValues: {
      workout_type: '',
      duration_minutes: 60,
      date: new Date().toISOString().split('T')[0],
      exercises: [],
    }
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "exercises"
  });

  useEffect(() => {
    if (workout) {
      reset({
        workout_type: workout.workout_type ?? '',
        duration_minutes: workout.duration_minutes ?? 60,
        date: workout.date.split('T')[0],
        exercises: workout.exercises.map(ex => ({
          exercise_title: ex.exercise_title,
          sets: ex.sets.map(s => ({
            reps: s.reps ?? 0,
            weight_kg: s.weight_kg ?? 0,
            set_index: s.set_index
          }))
        })),
      });
    } else {
      reset({
        workout_type: '',
        duration_minutes: 60,
        date: new Date().toISOString().split('T')[0],
        exercises: [],
      });
    }
  }, [workout, reset, isOpen]);

  const onSubmit = async (_data: WorkoutFormData) => {
    try {
      // Mock saving logic
      // Saving workout handled via context/store
      await fetchWorkouts();
      onClose();
    } catch { /* Handle error */ }
  };

  return (
    <PremiumDrawer
      isOpen={isOpen}
      onClose={onClose}
      title={workout ? t('workouts.edit_workout') : t('workouts.register_workout')}
      subtitle={workout ? workout.date.split('T')[0] : t('workouts.subtitle')}
      icon={<Dumbbell size={24} />}
    >
      <form onSubmit={(e) => { void handleSubmit(onSubmit)(e); }} className="space-y-8">
        
        {/* BASIC INFO */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FormField label={t('workouts.workout_type')} id="workout-type" icon={<Activity size={14} />} error={errors.workout_type?.message}>
            <Input id="workout-type" {...register('workout_type')} placeholder="Ex: Musculação" className="h-14 bg-white/5 border-white/5 rounded-2xl font-bold" />
          </FormField>
          
          <FormField label={t('workouts.duration')} id="workout-duration" icon={<Clock size={14} />} error={errors.duration_minutes?.message}>
            <Input id="workout-duration" type="number" {...register('duration_minutes', { valueAsNumber: true })} placeholder="Minutos" className="h-14 bg-white/5 border-white/5 rounded-2xl font-bold" />
          </FormField>
        </div>

        {/* EXERCISES SECTION */}
        <div className="space-y-6">
          <div className="flex items-center justify-between pb-2 border-b border-white/5">
            <div className="flex items-center gap-2">
              <Dumbbell size={18} className="text-indigo-400" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">{t('workouts.exercises')}</h3>
            </div>
            <button 
              type="button"
              onClick={() => { append({ exercise_title: '', sets: [{ reps: 10, weight_kg: 0, set_index: 0 }] }); }}
              className="text-[10px] font-black uppercase text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition-colors"
            >
              <Plus size={14} /> Adicionar
            </button>
          </div>

          <div className="space-y-4">
            {fields.map((field, index) => (
              <div key={field.id} className="p-6 rounded-3xl bg-white/5 border border-white/5 space-y-4 relative group/item hover:border-white/10 transition-all">
                <div className="flex items-center gap-3">
                  <Input 
                    // eslint-disable-next-line @typescript-eslint/restrict-template-expressions
                    {...register(`exercises.${index}.exercise_title`)} 
                    placeholder="Nome do Exercício" 
                    className="flex-1 h-10 bg-transparent border-transparent focus:border-white/10 font-bold"
                  />
                  <button type="button" onClick={() => { remove(index); }} className="p-2 text-zinc-600 hover:text-red-400 opacity-0 group-hover/item:opacity-100 transition-opacity">
                    <Trash2 size={16} />
                  </button>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                   <div className="flex items-center gap-2 bg-black/20 p-2 rounded-xl border border-white/5">
                      <span className="text-[10px] font-black text-zinc-500 uppercase ml-2">Carga</span>
                      {/* eslint-disable-next-line @typescript-eslint/restrict-template-expressions */}
                      <Input type="number" step="0.5" {...register(`exercises.${index}.sets.0.weight_kg`, { valueAsNumber: true })} className="h-8 bg-transparent border-transparent text-right font-black" />
                      <span className="text-[10px] font-black text-zinc-500 uppercase mr-2">kg</span>
                   </div>
                   <div className="flex items-center gap-2 bg-black/20 p-2 rounded-xl border border-white/5">
                      <span className="text-[10px] font-black text-zinc-500 uppercase ml-2">Reps</span>
                      {/* eslint-disable-next-line @typescript-eslint/restrict-template-expressions */}
                      <Input type="number" {...register(`exercises.${index}.sets.0.reps`, { valueAsNumber: true })} className="h-8 bg-transparent border-transparent text-right font-black" />
                   </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* SUBMIT */}
        <Button 
          type="submit" 
          fullWidth 
          isLoading={isSubmitting}
          className="btn-premium h-16"
        >
          <Save size={20} strokeWidth={3} />
          {t('common.save')}
        </Button>
      </form>
    </PremiumDrawer>
  );
}
