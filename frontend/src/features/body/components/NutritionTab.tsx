import {
  History,
  Flame,
  Beef,
  Wheat,
  Droplet
} from 'lucide-react';
import { Controller } from 'react-hook-form';

import { Button } from '../../../shared/components/ui/Button';
import { DataList } from '../../../shared/components/ui/DataList';
import { DateInput } from '../../../shared/components/ui/DateInput';
import { Input } from '../../../shared/components/ui/Input';
import { type NutritionLog } from '../../../shared/types/nutrition';
import { NutritionLogCard } from '../../nutrition/components/NutritionLogCard';
import { useNutritionTab } from '../hooks/useNutritionTab';

export function NutritionTab() {
  const {
    logs,
    isLoading,
    isSaving,
    currentPage,
    totalPages,
    register,
    control,
    handleSubmit,
    errors,
    deleteEntry,
    editEntry,
    changePage
  } = useNutritionTab();

  if (isLoading && logs.length === 0) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="h-64 bg-dark-card rounded-2xl" />
      </div>
    );
  }

  return (
    <div className="space-y-8 w-full overflow-x-hidden">
      {/* Entry Form - Full Width at Top */}
      <section className="bg-dark-card border border-border rounded-2xl p-4 md:p-6 shadow-sm w-full">
        <div className="flex items-center gap-2 pb-4 mb-4 border-b border-border">
          <Flame className="text-orange-500" size={24} />
          <h2 className="text-xl font-bold text-text-primary">Registrar Dieta</h2>
        </div>

        <form onSubmit={(e) => { void handleSubmit(e); }} className="flex flex-col gap-4 md:gap-6 w-full">
          <div className="w-full grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2 sm:gap-3 md:gap-4 lg:gap-6">
            <Controller
              name="date"
              control={control}
              render={({ field }) => (
                <DateInput
                  label="Data"
                  value={field.value}
                  onChange={field.onChange}
                  onBlur={field.onBlur}
                  error={errors.date?.message}
                />
              )}
            />
            <Input 
              id="calories"
              label="Calorias (kcal)" 
              type="number" 
              step="0.1"
              placeholder="Ex: 2100" 
              error={errors.calories?.message}
              {...register('calories', { valueAsNumber: true })}
            />
            <Input 
              id="protein_grams"
              label="Proteínas (g)" 
              type="number" 
              step="0.1"
              error={errors.protein_grams?.message}
              {...register('protein_grams', { valueAsNumber: true })}
              leftIcon={<Beef size={14} />}
            />
            <Input 
              id="carbs_grams"
              label="Carboidratos (g)" 
              type="number" 
              step="0.1"
              error={errors.carbs_grams?.message}
              {...register('carbs_grams', { valueAsNumber: true })}
              leftIcon={<Wheat size={14} />}
            />
            <Input 
              id="fat_grams"
              label="Gorduras (g)" 
              type="number" 
              step="0.1"
              error={errors.fat_grams?.message}
              {...register('fat_grams', { valueAsNumber: true })}
              leftIcon={<Droplet size={14} />}
            />
          </div>

          <div className="flex justify-end">
            <Button variant="primary" type="submit" isLoading={isSaving} className="shadow-orange w-full md:w-auto md:px-12">
              Salvar Registro
            </Button>
          </div>
        </form>
      </section>

      <DataList
        title={
          <div className="flex items-center gap-2">
            <History className="text-gradient-start" size={24} />
            <span>Histórico Recente</span>
          </div>
        }
        data={logs}
        isLoading={isLoading}
        renderItem={(log: NutritionLog) => (
          <NutritionLogCard 
            log={log} 
            onDelete={(id) => { void deleteEntry(id); }} 
            onEdit={editEntry}
          />
        )}
        keyExtractor={(item: NutritionLog) => item.id}
        layout="list"
        emptyState={{
          title: "Nenhum registro encontrado.",
          description: "Seus registros nutricionais aparecerão aqui."
        }}
        pagination={{
          currentPage: currentPage,
          totalPages: totalPages,
          onPageChange: (newPage: number) => { changePage(newPage); }
        }}
      />
    </div>
  );
}
