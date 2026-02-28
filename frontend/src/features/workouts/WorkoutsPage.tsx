import { Dumbbell, Plus, Search } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Button } from '../../shared/components/ui/Button';
import { DataList } from '../../shared/components/ui/DataList';
import { Input } from '../../shared/components/ui/Input';
import { useConfirmation } from '../../shared/hooks/useConfirmation';
import { useNotificationStore } from '../../shared/hooks/useNotification';
import { useWorkoutStore } from '../../shared/hooks/useWorkout';
import { mapWorkoutLogToWorkout } from '../../shared/utils/workout-mapper';

import { WorkoutCard } from './components/WorkoutCard';
import { WorkoutDrawer } from './components/WorkoutDrawer';

export function WorkoutsPage() {
  const { 
    workouts, 
    isLoading, 
    fetchWorkouts, 
    deleteWorkout,
    totalPages,
    page: currentPage,
    selectedWorkout,
    setSelectedWorkout
  } = useWorkoutStore();
  
  const { confirm } = useConfirmation();
  const notify = useNotificationStore();
  const { t } = useTranslation();
  
  const [searchTerm, setSearchTerm] = useState('');
  
  useEffect(() => {
    void fetchWorkouts();
  }, [fetchWorkouts]);

  const handleDelete = async (id: string) => {
    const isConfirmed = await confirm({
      title: t('workouts.delete_confirm_title'),
      message: t('workouts.delete_confirm_message'),
      confirmText: t('workouts.delete_confirm_btn'),
      type: 'danger',
    });

    if (isConfirmed) {
      try {
        await deleteWorkout(id);
        notify.success(t('workouts.delete_success'));
      } catch {
        notify.error(t('workouts.delete_error'));
      }
    }
  };

  const filteredWorkouts = workouts.filter((w) => 
    (w.workout_type ?? t('workouts.general_training')).toLowerCase().includes(searchTerm.toLowerCase()) ||
    w.exercises.some(ex => ex.name.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl font-bold text-text-primary flex items-center gap-3">
            <Dumbbell className="text-gradient-start" size={32} />
            {t('workouts.title')}
          </h1>
          <p className="text-text-secondary mt-1">
            {t('workouts.subtitle')}
          </p>
        </div>
        <Button variant="primary" size="lg" className="shadow-orange gap-2 hidden">
          <Plus size={20} />
          {t('workouts.new_workout')}
        </Button>
      </div>


      <DataList
        data={filteredWorkouts}
        isLoading={isLoading}
        renderItem={(workout) => (
          <WorkoutCard 
            workout={mapWorkoutLogToWorkout(workout)} 
            onDelete={(id) => {
              void handleDelete(id);
            }}
            onClick={() => { setSelectedWorkout(workout); }}
          />
        )}
        keyExtractor={(item) => item.id}
        layout="list"
        emptyState={{
          icon: <Dumbbell size={32} />,
          title: t('workouts.empty_title'),
          description: searchTerm 
            ? t('workouts.empty_search_desc')
            : t('workouts.empty_desc'),
          action: !searchTerm ? (
            <Button variant="primary">
              {t('workouts.register_first')}
            </Button>
          ) : undefined
        }}
        pagination={{
          currentPage,
          totalPages,
          onPageChange: (page) => void fetchWorkouts(page)
        }}
        headerContent={
           <div className="flex flex-col md:flex-row gap-4 mb-6">
            <div className="relative flex-1">
              <Input
                placeholder={t('workouts.search_placeholder')}
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                }}
                leftIcon={<Search size={18} />}
              />
            </div>
          </div>
        }
      />

      <WorkoutDrawer 
        workout={selectedWorkout ? mapWorkoutLogToWorkout(selectedWorkout) : null}
        isOpen={!!selectedWorkout}
        onClose={() => { setSelectedWorkout(null); }}
      />
    </div>
  );
}
