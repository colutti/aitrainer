import { Calendar, Clock, Dumbbell, Edit2, Trash2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { Button } from '../../../shared/components/ui/Button';
import { HistoryLogCard } from '../../../shared/components/ui/premium/HistoryLogCard';
import { type Workout } from '../../../shared/types/workout';
import { formatDate } from '../../../shared/utils/format-date';

interface WorkoutCardProps {
  workout: Workout;
  isReadOnly?: boolean;
  onDelete?: (id: string) => void;
  onEdit?: (workout: Workout) => void;
  onClick?: (workout: Workout) => void;
}

/**
 * WorkoutCard component
 * 
 * Displays a compact workout row for quick scanning.
 */
export function WorkoutCard({ workout, isReadOnly = false, onDelete, onEdit, onClick }: WorkoutCardProps) {
  const { t } = useTranslation();

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDelete) {
      onDelete(workout.id);
    }
  };

  const totalVolume = workout.exercises.reduce((acc, ex) => {
    return acc + ex.sets.reduce((sum, set) => sum + ((set.reps ?? 0) * (set.weight_kg ?? 0)), 0);
  }, 0);

  const workoutType = workout.workout_type
    ?? (workout.source === 'hevy' ? t('workouts.synced_label') : t('workouts.general_training'));
  const formattedTotalVolume = totalVolume >= 1000 ? (totalVolume / 1000).toFixed(1) : totalVolume.toLocaleString();
  const volumeUnit = totalVolume >= 1000 ? t('workouts.unit_ton') : t('workouts.unit_kg');

  return (
    <HistoryLogCard
      onClick={() => { onClick?.(workout); }}
      dataTestId="workout-card"
      icon={<Dumbbell size={22} />}
      title={workoutType}
      subtitle={(
        <span className="inline-flex items-center gap-1 text-xs text-zinc-400">
          <Calendar size={12} />
          {formatDate(workout.date)}
        </span>
      )}
      leadingMeta={(
        <span className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-black uppercase tracking-wider text-cyan-300 bg-cyan-400/10">
          <Clock size={12} />
          {workout.duration_minutes ?? '--'} min
        </span>
      )}
      metrics={[
        {
          label: t('workouts.exercises'),
          value: <span className="text-sm font-black text-emerald-400 tabular-nums">{workout.exercises.length}</span>,
        },
        {
          label: t('workouts.total_volume'),
          value: (
            <span className="text-sm font-black text-orange-400 tabular-nums">
              {formattedTotalVolume}
              <span className="ml-1 text-[10px] opacity-80">{volumeUnit}</span>
            </span>
          ),
        },
      ]}
      notes={workout.notes ? `"${workout.notes}"` : undefined}
      actions={(
        <>
          {!isReadOnly && onEdit && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={(e) => { e.stopPropagation(); onEdit(workout); }}
              className="h-9 w-9 rounded-full text-zinc-400 hover:bg-white/10 hover:text-white"
              title={t('shared.edit')}
              aria-label={t('shared.edit')}
            >
              <Edit2 size={16} />
            </Button>
          )}
          {!isReadOnly && onDelete && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={handleDelete}
              data-testid="btn-delete-workout"
              className="h-9 w-9 rounded-full text-red-300 hover:bg-red-500/15 hover:text-red-100"
              title={t('workouts.delete_confirm_btn')}
              aria-label={t('workouts.delete_confirm_btn')}
            >
              <Trash2 size={16} />
            </Button>
          )}
        </>
      )}
    />
  );
}
