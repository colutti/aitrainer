import {
  History,
  Flame,
  Beef,
  Wheat,
  Droplet,
  Pencil,
  X
} from 'lucide-react';
import { Controller } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

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
    cancelEdit,
    isEditing,
    editingId,
    changePage
  } = useNutritionTab();
  const { t } = useTranslation();

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
      <section key={editingId ?? 'new'} className="bg-dark-card border border-border rounded-2xl p-4 md:p-6 shadow-sm w-full">
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-border">
          <div className="flex items-center gap-2">
            {isEditing ? (
              <Pencil className="text-amber-400" size={24} />
            ) : (
              <Flame className="text-orange-500" size={24} />
            )}
            <h2 className="text-xl font-bold text-text-primary">
              {isEditing ? t('body.nutrition.edit_title') : t('body.nutrition.register_title')}
            </h2>
          </div>
          {isEditing && (
            <button
              type="button"
              onClick={cancelEdit}
              className="flex items-center gap-1 text-sm text-text-secondary hover:text-red-400 transition-colors"
            >
              <X size={16} />
              {t('body.nutrition.cancel')}
            </button>
          )}
        </div>

        <form onSubmit={(e) => { void handleSubmit(e); }} className="flex flex-col gap-4 md:gap-6 w-full">
          <div className="w-full grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2 sm:gap-3 md:gap-4 lg:gap-6">
            <Controller
              name="date"
              control={control}
              render={({ field }) => (
                <DateInput
                  label={t('body.nutrition.date')}
                  value={field.value}
                  onChange={field.onChange}
                  onBlur={field.onBlur}
                  error={errors.date?.message}
                />
              )}
            />
            <Input 
              id="calories"
              label={t('body.nutrition.calories')} 
              type="number" 
              step="0.1"
              placeholder={t('body.nutrition.calories_placeholder')} 
              error={errors.calories?.message}
              {...register('calories', { valueAsNumber: true })}
            />
            <Input 
              id="protein_grams"
              label={t('body.nutrition.protein')} 
              type="number" 
              step="0.1"
              error={errors.protein_grams?.message}
              {...register('protein_grams', { valueAsNumber: true })}
              leftIcon={<Beef size={14} />}
            />
            <Input 
              id="carbs_grams"
              label={t('body.nutrition.carbs')} 
              type="number" 
              step="0.1"
              error={errors.carbs_grams?.message}
              {...register('carbs_grams', { valueAsNumber: true })}
              leftIcon={<Wheat size={14} />}
            />
            <Input 
              id="fat_grams"
              label={t('body.nutrition.fat')} 
              type="number" 
              step="0.1"
              error={errors.fat_grams?.message}
              {...register('fat_grams', { valueAsNumber: true })}
              leftIcon={<Droplet size={14} />}
            />
          </div>

          <div className="flex justify-end">
            <Button variant="primary" type="submit" isLoading={isSaving} className="shadow-orange w-full md:w-auto md:px-12">
              {t('body.nutrition.save')}
            </Button>
          </div>
        </form>
      </section>

      <DataList
        title={
          <div className="flex items-center gap-2">
            <History className="text-gradient-start" size={24} />
            <span>{t('body.nutrition.history_title')}</span>
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
          title: t('body.nutrition.empty_title'),
          description: t('body.nutrition.empty_desc')
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
