import { Dumbbell, Trash2, ChevronRight, Calendar, Clock } from 'lucide-react';

import { PremiumCard } from '../../../shared/components/ui/premium/PremiumCard';
import { type Workout } from '../../../shared/types/workout';
import { formatDate } from '../../../shared/utils/format-date';

interface WorkoutCardProps {
  workout: Workout;
  onDelete?: (id: string) => void;
  onClick?: (workout: Workout) => void;
}

/**
 * WorkoutCard component
 * 
 * Displays a summary of a workout session with premium Glassmorphism aesthetic.
 */
export function WorkoutCard({ workout, onDelete, onClick }: WorkoutCardProps) {
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDelete) {
      onDelete(workout.id);
    }
  };

  const totalVolume = workout.exercises.reduce((acc, ex) => {
    return acc + ex.sets.reduce((sum, set) => sum + ((set.reps ?? 0) * (set.weight_kg ?? 0)), 0);
  }, 0);

  const workoutType = workout.workout_type ?? (workout.source === 'hevy' ? 'Sincronizado' : 'Treino Geral');

  return (
    <PremiumCard 
      onClick={() => onClick?.(workout)}
      data-testid="workout-card"
      className="p-6 md:p-8 cursor-pointer group flex flex-col justify-between min-h-[180px]"
    >
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-zinc-900 border border-white/5 flex items-center justify-center text-indigo-400 group-hover:text-emerald-400 transition-colors shadow-inner">
            <Dumbbell size={24} />
          </div>
          <div>
            <h3 className="text-xl font-black text-white group-hover:translate-x-1 transition-transform">
              {workoutType}
            </h3>
            <div className="flex items-center gap-3 mt-1 text-zinc-500 font-bold text-[10px] uppercase tracking-widest">
               <span className="flex items-center gap-1"><Calendar size={12}/> {formatDate(workout.date)}</span>
               <span className="flex items-center gap-1"><Clock size={12}/> {workout.duration_minutes ?? '--'} min</span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {onDelete && (
            <button 
              onClick={handleDelete}
              data-testid="btn-delete-workout"
              className="p-2 rounded-full bg-red-500/10 text-red-500 opacity-0 group-hover:opacity-100 transition-all hover:bg-red-500/20"
              title="Excluir treino"
              aria-label="Delete"
            >
              <Trash2 size={18} />
            </button>
          )}
          <div className="p-2 rounded-full bg-white/5 text-zinc-500 group-hover:text-white group-hover:bg-white/10 transition-all">
             <ChevronRight size={20} />
          </div>
        </div>
      </div>

      <div className="flex items-end justify-between mt-4">
        <div className="flex flex-wrap gap-2">
           {workout.exercises.slice(0, 3).map((ex, idx) => (
             <span key={idx} className="px-3 py-1 rounded-full bg-white/5 border border-white/5 text-[10px] font-bold text-zinc-400">
                {ex.exercise_title}
             </span>
           ))}
           {workout.exercises.length > 3 && (
             <span className="px-3 py-1 rounded-full bg-white/5 text-[10px] font-bold text-zinc-500">
                +{workout.exercises.length - 3}
             </span>
           )}
        </div>

        <div className="text-right">
           <p className="text-[9px] uppercase font-black text-zinc-600 tracking-widest mb-0.5">Volume Total</p>
           <p className="text-lg font-black text-orange-400 tabular-nums leading-none">
              {totalVolume >= 1000 ? (totalVolume / 1000).toFixed(1) : totalVolume.toLocaleString()}
              <span className="text-[10px] ml-0.5 opacity-60 font-bold">{totalVolume >= 1000 ? 't' : 'kg'}</span>
           </p>
        </div>
      </div>
    </PremiumCard>
  );
}
