import { Dumbbell, Plus } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { EntityListScreen } from '../../../shared/components/layout/EntityListScreen';
import { DataList } from '../../../shared/components/ui/DataList';
import { PREMIUM_UI } from '../../../shared/styles/ui-variants';
import { type Workout } from '../../../shared/types/workout';
import { cn } from '../../../shared/utils/cn';

import { WorkoutCard } from './WorkoutCard';

interface WorkoutsViewProps {
  workouts: Workout[];
  isLoading: boolean;
  currentPage: number;
  totalPages: number;
  isReadOnly?: boolean;
  onRegisterWorkout: () => void;
  onDeleteWorkout: (id: string) => void;
  onEditWorkout: (workout: Workout) => void;
  onSelectWorkout: (workout: Workout) => void;
  onPageChange: (page: number) => void;
}

/**
 * WorkoutsView component
 * 
 * Refactored to use DataView orchestrator and shared Premium components.
 */
export function WorkoutsView({ 
  workouts, 
  isLoading, 
  currentPage,
  totalPages,
  isReadOnly = false,
  onRegisterWorkout, 
  onDeleteWorkout,
  onEditWorkout,
  onSelectWorkout,
  onPageChange,
}: WorkoutsViewProps) {
  const { t } = useTranslation();

  return (
    <div className={cn(PREMIUM_UI.animation.fadeIn, 'space-y-8 pb-20')} data-testid="workouts-list-screen">
      <EntityListScreen
        title={t('workouts.title')}
        subtitle={t('workouts.subtitle')}
        actions={
          <button
            type="button"
            onClick={onRegisterWorkout}
            disabled={isReadOnly}
            className={cn(
              PREMIUM_UI.button.premium,
              'inline-flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            <Plus size={16} />
            {t('workouts.register_workout')}
          </button>
        }
        list={
          <DataList
            data={workouts}
            renderItem={(workout) => (
              <WorkoutCard
                workout={workout}
                isReadOnly={isReadOnly}
                onDelete={onDeleteWorkout}
                onEdit={onEditWorkout}
                onClick={onSelectWorkout}
              />
            )}
            keyExtractor={(workout) => workout.id}
            isLoading={isLoading}
            layout="list"
            emptyState={{
              title: t('workouts.empty_title'),
              description: t('workouts.empty_desc'),
              icon: <Dumbbell size={40} className="text-zinc-500" />,
            }}
            pagination={{
              currentPage,
              totalPages,
              onPageChange,
            }}
            className="space-y-8"
            gridClassName="grid-cols-1"
          />
        }
      />
    </div>
  );
}
