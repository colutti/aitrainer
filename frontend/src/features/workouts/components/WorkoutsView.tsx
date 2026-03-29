import { Dumbbell, Plus } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { DataView } from '../../../shared/components/ui/premium/DataView';
import { ViewHeader } from '../../../shared/components/ui/premium/ViewHeader';
import { Skeleton } from '../../../shared/components/ui/Skeleton';
import { PREMIUM_UI } from '../../../shared/styles/ui-variants';
import { type Workout } from '../../../shared/types/workout';
import { cn } from '../../../shared/utils/cn';

import { WorkoutCard } from './WorkoutCard';

interface WorkoutsViewProps {
  workouts: Workout[];
  isLoading: boolean;
  error?: unknown;
  isReadOnly?: boolean;
  onRegisterWorkout: () => void;
  onDeleteWorkout: (id: string) => void;
  onSelectWorkout: (workout: Workout) => void;
  onRetry?: () => void;
}

/**
 * WorkoutsView component
 * 
 * Refactored to use DataView orchestrator and shared Premium components.
 */
export function WorkoutsView({ 
  workouts, 
  isLoading, 
  error,
  isReadOnly = false,
  onRegisterWorkout, 
  onDeleteWorkout,
  onSelectWorkout,
  onRetry
}: WorkoutsViewProps) {
  const { t } = useTranslation();

  const loadingSkeleton = (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-pulse">
      {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-48 rounded-[32px] bg-white/5" />)}
    </div>
  );

  return (
    <div className={cn(PREMIUM_UI.animation.fadeIn, "space-y-8 pb-20")}>
      
      {/* HEADER */}
      <ViewHeader 
        title={t('workouts.title')}
        subtitle={t('workouts.subtitle')}
        action={{
          label: t('workouts.register_workout'),
          icon: <Plus size={20} strokeWidth={3} />,
          onClick: onRegisterWorkout,
          disabled: isReadOnly,
        }}
      />

      {/* DATA ORCHESTRATION LAYER */}
      <DataView
        isLoading={isLoading && workouts.length === 0}
        error={error}
        isEmpty={workouts.length === 0}
        onRetry={onRetry}
        loadingSkeleton={loadingSkeleton}
        emptyState={{
          title: t('workouts.empty_title'),
          description: t('workouts.empty_desc'),
          icon: <Dumbbell size={40} className="text-zinc-500" />
        }}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {workouts.map(workout => (
            <WorkoutCard 
              key={workout.id} 
              workout={workout} 
              isReadOnly={isReadOnly}
              onDelete={onDeleteWorkout}
              onClick={onSelectWorkout}
            />
          ))}
        </div>
      </DataView>
    </div>
  );
}
