import { useEffect, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';

import { useConfirmation } from '../../shared/hooks/useConfirmation';
import { useNotificationStore } from '../../shared/hooks/useNotification';
import { useWorkoutStore } from '../../shared/hooks/useWorkout';
import { type Workout } from '../../shared/types/workout';
import { mapWorkoutLogToWorkout } from '../../shared/utils/workout-mapper';

import { WorkoutDrawer } from './components/WorkoutDrawer';
import { WorkoutsView } from './components/WorkoutsView';

/**
 * WorkoutsPage component (Container)
 * 
 * Manages workouts state and interactions using the global store.
 */
export default function WorkoutsPage() {
  const { 
    workouts, 
    isLoading, 
    error,
    fetchWorkouts, 
    deleteWorkout 
  } = useWorkoutStore();
  
  const { t } = useTranslation();
  const confirm = useConfirmation();
  const notify = useNotificationStore();
  
  const [selectedWorkout, setSelectedWorkout] = useState<Workout | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  useEffect(() => {
    void fetchWorkouts();
  }, [fetchWorkouts]);

  const handleRegisterWorkout = useCallback(() => {
    setSelectedWorkout(null);
    setIsDrawerOpen(true);
  }, []);

  const handleSelectWorkout = useCallback((workout: Workout) => {
    setSelectedWorkout(workout);
    setIsDrawerOpen(true);
  }, []);

  const handleDeleteWorkout = useCallback((id: string) => {
    const run = async () => {
      const confirmed = await confirm.confirm({
        title: t('workouts.delete_confirm_title'),
        message: t('workouts.delete_confirm_message'),
        confirmText: t('workouts.delete_confirm_btn'),
      });

      if (confirmed) {
        try {
          await deleteWorkout(id);
          notify.success(t('workouts.delete_success'));
        } catch {
          notify.error(t('workouts.delete_error'));
        }
      }
    };
    void run();
  }, [confirm, deleteWorkout, notify, t]);

  // Map workout logs to workout objects for the view
  const workoutList: Workout[] = workouts.map(mapWorkoutLogToWorkout);

  return (
    <>
      <WorkoutsView 
        workouts={workoutList}
        isLoading={isLoading}
        error={error}
        onRegisterWorkout={handleRegisterWorkout}
        onDeleteWorkout={handleDeleteWorkout}
        onSelectWorkout={handleSelectWorkout}
        onRetry={() => { void fetchWorkouts(); }}
      />

      <WorkoutDrawer 
        workout={selectedWorkout}
        isOpen={isDrawerOpen}
        onClose={() => { setIsDrawerOpen(false); setSelectedWorkout(null); }}
      />
    </>
  );
}
