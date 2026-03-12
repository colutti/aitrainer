import { Dumbbell, Trash2, ChevronRight } from 'lucide-react';

import { Button } from '../../../shared/components/ui/Button';
import { type Workout } from '../../../shared/types/workout';
import { cn } from '../../../shared/utils/cn';
import { formatDate } from '../../../shared/utils/format-date';

interface WorkoutCardProps {
  workout: Workout;
  onDelete?: (id: string) => void;
  onClick?: (workout: Workout) => void;
}

/**
 * WorkoutCard component
 * 
 * Displays a summary of a workout session with premium styling in a columnar layout,
 * matching the style of weight and nutrition logs.
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

  // Extract workout type
  const workoutType = workout.workout_type ?? (workout.source === 'hevy' ? 'Sincronizado' : 'Treino Geral');

  return (
    <div 
      onClick={() => onClick?.(workout)}
      className={cn(
        "bg-dark-card border border-border/50 rounded-2xl p-4 hover:border-gradient-start/40 transition-all duration-300 group flex items-center gap-5 w-full hover:bg-white/5 active:scale-[0.99] relative overflow-hidden",
        onClick && "cursor-pointer"
      )}
    >
      {/* Accent Line */}
      <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-start opacity-0 group-hover:opacity-100 transition-opacity" />

      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-gradient-start/10 to-gradient-end/10 flex flex-shrink-0 items-center justify-center text-gradient-start group-hover:scale-110 transition-transform duration-500 shadow-inner">
        <Dumbbell size={22} />
      </div>
      
      <div className="flex-1 min-w-0 grid grid-cols-1 md:grid-cols-12 gap-4 md:gap-6 items-center">
        {/* Date and Type Section */}
        <div className="md:col-span-4 min-w-0 flex flex-col justify-center">
           <h3 className="font-black text-text-primary text-base leading-tight tracking-tight group-hover:text-white transition-colors">
            {formatDate(workout.date)}
           </h3>
           <div className="flex items-center gap-2 mt-1">
              <span className="text-[11px] font-bold text-text-muted flex items-center gap-1.5 uppercase tracking-wider">
                {workoutType}
              </span>
              {workout.source === 'hevy' && (
                <span className="text-[8px] bg-blue-500/10 text-blue-400 px-1.5 py-0.5 rounded-md font-bold uppercase tracking-widest border border-blue-500/10">
                  Hevy
                </span>
              )}
           </div>
        </div>

        {/* Details Section - Table Style Alignment */}
        <div className="md:col-span-5 grid grid-cols-3 gap-0 md:border-l md:border-white/5 md:pl-6">
             <div className="flex flex-col items-center md:items-end">
                <p className="text-[9px] uppercase font-black text-[#666] tracking-[0.15em] mb-1">Exer.</p>
                <p className="text-sm font-black text-white tabular-nums">{workout.exercises.length}</p>
             </div>
             <div className="flex flex-col items-center md:items-end border-l border-white/5 pr-4">
                <p className="text-[9px] uppercase font-black text-[#666] tracking-[0.15em] mb-1">Volume</p>
                <p className="text-sm font-black text-orange-400 tabular-nums">
                  {totalVolume >= 1000 ? (totalVolume / 1000).toFixed(1) : totalVolume.toLocaleString()}
                  <span className="text-[10px] ml-0.5 opacity-60 font-bold">{totalVolume >= 1000 ? 't' : 'kg'}</span>
                </p>
             </div>
             <div className="flex flex-col items-center md:items-end border-l border-white/5">
                <p className="text-[9px] uppercase font-black text-[#666] tracking-[0.15em] mb-1">Tempo</p>
                <p className="text-sm font-black text-blue-400 tabular-nums">
                  {workout.duration_minutes ?? '--'}
                  <span className="text-[10px] ml-0.5 opacity-60 font-bold">min</span>
                </p>
             </div>
        </div>
        
        {/* Actions - Right */}
        <div className="md:col-span-3 flex justify-end items-center gap-4">
            <Button 
              variant="danger" 
              size="icon" 
              onClick={handleDelete}
              className="opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-all hover:scale-110 hover:shadow-red bg-red-500/10 border-red-500/20"
              title="Excluir treino"
            >
              <Trash2 size={16} />
            </Button>
            <div className="text-text-muted/30 hidden sm:block group-hover:text-gradient-start group-hover:translate-x-1 transition-all">
              <ChevronRight size={22} />
            </div>
        </div>
      </div>
    </div>
  );
}

