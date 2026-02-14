import { X } from 'lucide-react';

import { Button } from '../../../shared/components/ui/Button';
import type { Workout } from '../../../shared/types/workout';
import { cn } from '../../../shared/utils/cn';
import { formatDate } from '../../../shared/utils/format-date';

interface WorkoutDrawerProps {
  workout: Workout | null;
  isOpen: boolean;
  onClose: () => void;
}

/**
 * Drawer component to display workout details with exercises
 * Slides in from the right side of the screen
 */
export function WorkoutDrawer({ workout, isOpen, onClose }: WorkoutDrawerProps) {
  if (!workout) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className={cn(
          'fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity',
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        )}
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className={cn(
          'fixed right-0 top-0 h-full w-full md:w-[500px] bg-dark-card border-l border-border z-50',
          'transform transition-transform duration-300 ease-in-out overflow-y-auto',
          isOpen ? 'translate-x-0' : 'translate-x-full'
        )}
      >
        {/* Header */}
        <div className="sticky top-0 bg-dark-card/95 backdrop-blur-md border-b border-border p-6 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-text-primary">Detalhes do Treino</h2>
            <p className="text-sm text-text-secondary mt-1">
              {formatDate(workout.date, 'full')}
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="text-text-muted hover:text-text-primary"
          >
            <X size={20} />
          </Button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Summary */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-zinc-900/50 p-4 rounded-xl">
              <p className="text-xs text-text-muted mb-1">Total de Exercícios</p>
              <p className="text-2xl font-bold text-gradient-start">{workout.exercises.length}</p>
            </div>
            <div className="bg-zinc-900/50 p-4 rounded-xl">
              <p className="text-xs text-text-muted mb-1">Duração</p>
              <p className="text-2xl font-bold text-gradient-end">
                {workout.duration_minutes ? `${String(workout.duration_minutes)}min` : 'N/A'}
              </p>
            </div>
          </div>

          {/* Exercises List */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wide">
              Exercícios
            </h3>
            
            {workout.exercises.map((exercise, idx) => (
              <div
                key={exercise.exercise_id ?? idx}
                className="bg-zinc-900/30 border border-zinc-800 rounded-xl p-4 space-y-3"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="font-semibold text-text-primary">{exercise.exercise_title}</h4>
                    {exercise.notes && (
                      <p className="text-xs text-text-muted mt-1">{exercise.notes}</p>
                    )}
                  </div>
                  <span className="text-xs px-2 py-1 bg-gradient-start/10 text-gradient-start rounded-full">
                    {exercise.sets.length} séries
                  </span>
                </div>

                {/* Sets */}
                <div className="space-y-2">
                  {exercise.sets.map((set, setIdx) => (
                    <div
                      key={setIdx}
                      className="flex items-center justify-between text-sm bg-zinc-900/50 px-3 py-2 rounded-lg"
                    >
                      <span className="text-text-secondary">Série {setIdx + 1}</span>
                      <div className="flex items-center gap-4 text-text-primary">
                        {set.distance_meters != null && (
                          <span className="font-mono text-blue-400">
                            {set.distance_meters}m
                          </span>
                        )}
                        {set.duration_seconds != null && (
                          <span className="font-mono text-cyan-400">
                            {(set.duration_seconds / 60).toFixed(1)}min
                          </span>
                        )}
                        {set.weight_kg != null && set.weight_kg > 0 && (
                          <span className="font-mono">
                            {set.weight_kg}kg
                          </span>
                        )}
                        {set.reps != null && set.reps > 0 && (
                          <span className="font-mono">
                            {set.reps} reps
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Exercise PRs */}
                {exercise.pr_data && Object.keys(exercise.pr_data).length > 0 && (
                  <div className="pt-2 border-t border-zinc-800">
                    <p className="text-xs text-yellow-500 font-semibold">
                      🏆 PRs: {Object.keys(exercise.pr_data).join(', ')}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Workout Notes */}
          {workout.notes && (
            <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-4">
              <h3 className="text-sm font-semibold text-blue-400 mb-2">Anotações</h3>
              <p className="text-sm text-text-primary">{workout.notes}</p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
