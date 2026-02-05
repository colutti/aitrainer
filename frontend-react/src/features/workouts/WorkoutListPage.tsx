import { Dumbbell, Filter, Plus, Search } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Button } from '../../shared/components/ui/Button';
import { Input } from '../../shared/components/ui/Input';
import { useConfirmation } from '../../shared/hooks/useConfirmation';
import { useNotificationStore } from '../../shared/hooks/useNotification';
import { useWorkoutStore } from '../../shared/hooks/useWorkout';

import { WorkoutCard } from './components/WorkoutCard';

/**
 * WorkoutListPage component
 * 
 * Displays a paginated list of workout logs with searching, filtering, 
 * and deletion capabilities.
 */
export function WorkoutListPage() {
  const { 
    workouts, 
    isLoading, 
    fetchWorkouts, 
    deleteWorkout,
    totalPages,
    page: currentPage
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

      {/* Filters & Search */}
      <div className="flex flex-col md:flex-row gap-4">
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

      {/* Workout Grid */}
      {isLoading && workouts.length === 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-pulse">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-48 bg-dark-card rounded-2xl" />
          ))}
        </div>
      ) : filteredWorkouts.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredWorkouts.map((workout) => (
            <WorkoutCard 
              key={workout.id} 
              workout={workout} 
              onDelete={(id) => {
                void handleDelete(id);
              }}
            />
          ))}
        </div>
      ) : (
        <div className="bg-dark-card border border-border border-dashed rounded-3xl p-12 text-center">
          <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-4 text-text-muted">
            <Dumbbell size={32} />
          </div>
          <h3 className="text-xl font-bold text-text-primary">Nenhum treino encontrado</h3>
          <p className="text-text-secondary mt-2 max-w-xs mx-auto">
            {searchTerm 
              ? 'Não encontramos resultados para sua busca.' 
              : 'Você ainda não registrou nenhum treino. Vamos começar hoje?'}
          </p>
          {!searchTerm && (
            <Button variant="primary" className="mt-6">
              Registrar Primeiro Treino
            </Button>
          )}
        </div>
      )}

      {/* Pagination (Simplified for now) */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2 pt-4">
          <Button 
            variant="secondary" 
            disabled={currentPage === 1 || isLoading}
            onClick={() => {
              void fetchWorkouts(currentPage - 1);
            }}
          >
            Anterior
          </Button>
          <div className="flex items-center px-4 font-medium text-text-secondary">
            Página {currentPage.toString()} de {totalPages.toString()}
          </div>
          <Button 
            variant="secondary"
            disabled={currentPage === totalPages || isLoading}
            onClick={() => {
              void fetchWorkouts(currentPage + 1);
            }}
          >
            Próxima
          </Button>
        </div>
      )}
    </div>
  );
}
