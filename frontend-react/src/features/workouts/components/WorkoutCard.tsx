import { Calendar, Clock, Dumbbell, Trash2, ChevronRight } from 'lucide-react';

import { Button } from '../../../shared/components/ui/Button';
import { type WorkoutLog } from '../../../shared/types/workout';
import { formatDate } from '../../../shared/utils/format-date';

interface WorkoutCardProps {
  workout: WorkoutLog;
  onDelete?: (id: string) => void;
  onClick?: (workout: WorkoutLog) => void;
}

/**
 * WorkoutCard component
 * 
 * Displays a summary of a workout session with premium styling.
 */
export function WorkoutCard({ workout, onDelete, onClick }: WorkoutCardProps) {
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDelete) {
      onDelete(workout.id);
    }
  };

  return (
    <div 
      onClick={() => onClick?.(workout)}
      className="bg-dark-card border border-border rounded-2xl p-5 hover:border-gradient-start/30 transition-all duration-300 group cursor-pointer"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-gradient-start/10 to-gradient-end/10 flex items-center justify-center text-gradient-start group-hover:scale-110 transition-transform duration-300">
            <Dumbbell size={24} />
          </div>
          <div>
            <h3 className="text-lg font-bold text-text-primary">
              {workout.workout_type ?? 'Treino Geral'}
            </h3>
            <div className="flex items-center gap-3 mt-1 text-sm text-text-secondary">
              <div className="flex items-center gap-1">
                <Calendar size={14} />
                {formatDate(workout.date)}
              </div>
              {workout.duration_minutes && (
                <div className="flex items-center gap-1 border-l border-border pl-3">
                  <Clock size={14} />
                  {workout.duration_minutes.toString()} min
                </div>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button 
            variant="danger" 
            size="icon" 
            onClick={handleDelete}
            title="Excluir treino"
          >
            <Trash2 size={16} />
          </Button>
          <div className="text-text-muted">
            <ChevronRight size={20} />
          </div>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-4">
        <div className="bg-dark-bg/50 rounded-xl p-3 border border-border/50">
          <p className="text-xs text-text-muted font-medium uppercase tracking-wider">Exercícios</p>
          <p className="text-lg font-bold text-text-primary">{workout.exercises.length.toString()}</p>
        </div>
        <div className="bg-dark-bg/50 rounded-xl p-3 border border-border/50">
          <p className="text-xs text-text-muted font-medium uppercase tracking-wider">Volume Total</p>
          <p className="text-lg font-bold text-text-primary">
             {workout.exercises.reduce((acc, ex) => {
               const exVolume = ex.sets * ex.reps_per_set.reduce((rAcc, r) => rAcc + r, 0) * (ex.weights_per_set[0] ?? 0);
               return acc + exVolume;
             }, 0).toLocaleString()} kg
          </p>
        </div>
      </div>

      {workout.source === 'hevy' && (
        <div className="mt-4 flex items-center gap-2">
          <span className="text-[10px] bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded-full font-bold uppercase tracking-widest">
            Sincronizado via Hevy
          </span>
        </div>
      )}
    </div>
  );
}
