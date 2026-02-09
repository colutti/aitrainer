import { Dumbbell, Filter, Plus, Search } from 'lucide-react';
import { useEffect, useState } from 'react';

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
  
  const [searchTerm, setSearchTerm] = useState('');
  
  useEffect(() => {
    void fetchWorkouts();
  }, [fetchWorkouts]);

  const handleDelete = async (id: string) => {
    const isConfirmed = await confirm({
      title: 'Excluir Treino',
      message: 'Tem certeza que deseja excluir este registro de treino? Esta ação não pode ser desfeita.',
      confirmText: 'Excluir',
      type: 'danger',
    });

    if (isConfirmed) {
      try {
        await deleteWorkout(id);
        notify.success('Treino excluído com sucesso!');
      } catch {
        notify.error('Erro ao excluir treino.');
      }
    }
  };

  const filteredWorkouts = workouts.filter((w) => 
    (w.workout_type ?? 'Treino Geral').toLowerCase().includes(searchTerm.toLowerCase()) ||
    w.exercises.some(ex => ex.name.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl font-bold text-text-primary flex items-center gap-3">
            <Dumbbell className="text-gradient-start" size={32} />
            Meus Treinos
          </h1>
          <p className="text-text-secondary mt-1">
            Acompanhe sua evolução e mantenha a consistência.
          </p>
        </div>
        <Button variant="primary" size="lg" className="shadow-orange gap-2">
          <Plus size={20} />
          Novo Treino
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
          title: "Nenhum treino encontrado",
          description: searchTerm 
            ? 'Não encontramos resultados para sua busca.' 
            : 'Você ainda não registrou nenhum treino. Vamos começar hoje?',
          action: !searchTerm ? (
            <Button variant="primary">
              Registrar Primeiro Treino
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
                placeholder="Buscar por tipo ou exercício..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                }}
                leftIcon={<Search size={18} />}
              />
            </div>
            <div className="flex gap-2">
              <Button variant="secondary" className="gap-2">
                <Filter size={18} />
                Filtrar
              </Button>
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
