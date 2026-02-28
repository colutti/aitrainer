import {
  Scale,
  Pencil,
  X
} from 'lucide-react';
import { useState } from 'react';
import { Controller } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { Button } from '../../../shared/components/ui/Button';
import { DataList } from '../../../shared/components/ui/DataList';
import { DateInput } from '../../../shared/components/ui/DateInput';
import { Input } from '../../../shared/components/ui/Input';
import type { WeightLog } from '../../../shared/types/body';
import { useWeightTab } from '../hooks/useWeightTab';

import { WeightLogCard } from './WeightLogCard';
import { WeightLogDrawer } from './WeightLogDrawer';

export function WeightTab() {
  const [viewLog, setViewLog] = useState<WeightLog | null>(null);

  const {
    history,
    isLoading,
    isSaving,
    register,
    control,
    handleSubmit,
    errors,
    deleteEntry,
    editEntry,
    cancelEdit,
    isEditing,
    editingDate,
    page,
    totalPages,
    changePage
  } = useWeightTab();
  const { t } = useTranslation();

  if (isLoading && history.length === 0) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="h-64 bg-dark-card rounded-2xl" />
      </div>
    );
  }

  return (
    <div className="space-y-8 w-full overflow-x-hidden">
      {/* Entry Form - Full Width at Top */}
      <section key={editingDate ?? 'new'} className="bg-dark-card border border-border rounded-2xl p-4 md:p-6 shadow-sm w-full">
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-border">
          <div className="flex items-center gap-2">
            {isEditing ? (
              <Pencil className="text-amber-400" size={24} />
            ) : (
              <Scale className="text-gradient-start" size={24} />
            )}
            <h2 className="text-xl font-bold text-text-primary">
              {isEditing ? t('body.weight.edit_title') : t('body.weight.register_title')}
            </h2>
          </div>
          {isEditing && (
            <button
              type="button"
              onClick={cancelEdit}
              className="flex items-center gap-1 text-sm text-text-secondary hover:text-red-400 transition-colors"
            >
              <X size={16} />
              {t('body.weight.cancel')}
            </button>
          )}
        </div>

        <form onSubmit={(e) => { void handleSubmit(e); }} className="space-y-4 md:space-y-6">
          <div className="w-full grid grid-cols-1 sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-3 md:gap-4 lg:gap-6">
            <Controller
              name="date"
              control={control}
              render={({ field }) => (
                <DateInput
                  label={t('body.weight.date')}
                  value={field.value}
                  onChange={field.onChange}
                  onBlur={field.onBlur}
                  error={errors.date?.message}
                />
              )}
            />
            <Input 
              id="weight_kg"
              label={t('body.weight.weight')} 
              type="number" 
              step="0.01" 
              placeholder="Ex: 75.50" 
              error={errors.weight_kg?.message}
              {...register('weight_kg', { valueAsNumber: true })}
            />
            <Input 
              id="body_fat_pct"
              label={t('body.weight.body_fat')} 
              type="number" 
              step="0.01" 
              placeholder="Ex: 15.50"
              error={errors.body_fat_pct?.message}
              {...register('body_fat_pct', { valueAsNumber: true })}
            />
            <Input 
              id="muscle_mass_kg"
              label={t('body.weight.muscle_mass')} 
              type="number" 
              step="0.01" 
              placeholder="Ex: 35.20"
              error={errors.muscle_mass_kg?.message}
              {...register('muscle_mass_kg', { valueAsNumber: true })}
            />
            <Input 
              label={t('body.weight.body_water')} 
              type="number" 
              step="0.01" 
              placeholder="Ex: 55.50"
              error={errors.body_water_pct?.message}
              {...register('body_water_pct', { valueAsNumber: true })}
            />
            <Input 
              label={t('body.weight.bone_mass')} 
              type="number" 
              step="0.01" 
              placeholder="Ex: 3.50"
              error={errors.bone_mass_kg?.message}
              {...register('bone_mass_kg', { valueAsNumber: true })}
            />
            <Input 
              label={t('body.weight.visceral_fat')} 
              type="number" 
              step="0.01" 
              placeholder="Ex: 5.0"
              error={errors.visceral_fat?.message}
              {...register('visceral_fat', { valueAsNumber: true })}
            />
            <Input 
              label={t('body.weight.bmr')} 
              type="number" 
              step="0.1"
              placeholder="Ex: 1850"
              error={errors.bmr?.message}
              {...register('bmr', { valueAsNumber: true })}
            />
            <div className="md:col-span-2 lg:col-span-4">
              <Input 
                id="notes"
                label={t('body.weight.notes')} 
                type="text" 
                placeholder={t('body.weight.notes_placeholder')}
                error={errors.notes?.message}
                {...register('notes')}
              />
            </div>
          </div>

          {/* Measurements Section */}
          <div className="pt-6 border-t border-border">
            <h3 className="text-sm font-bold text-text-secondary uppercase tracking-wider mb-4">{t('body.weight.measurements_title')}</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2 sm:gap-3 md:gap-4 lg:gap-6">
              <Input label={t('body.weight.neck')} type="number" step="0.01" placeholder="Ex: 38" error={errors.neck_cm?.message} {...register('neck_cm', { valueAsNumber: true })} />
              <Input label={t('body.weight.chest')} type="number" step="0.01" placeholder="Ex: 100" error={errors.chest_cm?.message} {...register('chest_cm', { valueAsNumber: true })} />
              <Input id="waist_cm" label={t('body.weight.waist')} type="number" step="0.01" placeholder="Ex: 85" error={errors.waist_cm?.message} {...register('waist_cm', { valueAsNumber: true })} />
              <Input label={t('body.weight.hips')} type="number" step="0.01" placeholder="Ex: 95" error={errors.hips_cm?.message} {...register('hips_cm', { valueAsNumber: true })} />
              <Input label={t('body.weight.bicep_r')} type="number" step="0.01" placeholder="Ex: 35" error={errors.bicep_r_cm?.message} {...register('bicep_r_cm', { valueAsNumber: true })} />
              <Input label={t('body.weight.bicep_l')} type="number" step="0.01" placeholder="Ex: 35" error={errors.bicep_l_cm?.message} {...register('bicep_l_cm', { valueAsNumber: true })} />
              <Input label={t('body.weight.thigh_r')} type="number" step="0.01" placeholder="Ex: 55" error={errors.thigh_r_cm?.message} {...register('thigh_r_cm', { valueAsNumber: true })} />
              <Input label={t('body.weight.thigh_l')} type="number" step="0.01" placeholder="Ex: 55" error={errors.thigh_l_cm?.message} {...register('thigh_l_cm', { valueAsNumber: true })} />
              <Input label={t('body.weight.calf_r')} type="number" step="0.01" placeholder="Ex: 38" error={errors.calf_r_cm?.message} {...register('calf_r_cm', { valueAsNumber: true })} />
              <Input label={t('body.weight.calf_l')} type="number" step="0.01" placeholder="Ex: 38" error={errors.calf_l_cm?.message} {...register('calf_l_cm', { valueAsNumber: true })} />
            </div>
          </div>

          <div className="flex justify-end">
             <Button variant="primary" type="submit" isLoading={isSaving} className="shadow-orange w-full md:w-auto md:px-12">
              {t('body.weight.save')}
            </Button>
          </div>
        </form>
      </section>

      <DataList
        title={t('body.weight.history_title')}
        data={history}
        isLoading={isLoading}
        renderItem={(log) => (
          <WeightLogCard 
            log={log} 
            onDelete={(date) => { void deleteEntry(date); }} 
            onEdit={editEntry} 
            onClick={setViewLog}
          />
        )}
        keyExtractor={(item) => item.id ?? item.date}
        layout="list"
        emptyState={{
          title: t('body.weight.empty_title'),
          description: t('body.weight.empty_desc')
        }}
        pagination={{
            currentPage: page,
            totalPages: totalPages,
            onPageChange: (newPage) => { changePage(newPage); }
        }}
      />

      {/* Details Drawer */}
      <WeightLogDrawer 
        log={viewLog} 
        isOpen={!!viewLog} 
        onClose={() => { setViewLog(null); }} 
      />
    </div>
  );
}
