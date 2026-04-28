import { zodResolver } from '@hookform/resolvers/zod';
import { Flame, Beef, Wheat, Droplets, Pencil, Save, History, Calendar } from 'lucide-react';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { z } from 'zod';

import { Button } from '../../../shared/components/ui/Button';
import { Input } from '../../../shared/components/ui/Input';
import { FormField } from '../../../shared/components/ui/premium/FormField';
import { PremiumDrawer } from '../../../shared/components/ui/premium/PremiumDrawer';
import { type NutritionLog, type NutritionFormData } from '../../../shared/types/nutrition';
import { formatDate } from '../../../shared/utils/format-date';

const nutritionSchema = z.object({
  date: z.string().min(1, 'Data é obrigatória'),
  source: z.string().min(1),
  calories: z.coerce.number().min(0).max(10000),
  protein_grams: z.coerce.number().min(0).max(1000).optional().nullable(),
  carbs_grams: z.coerce.number().min(0).max(2000).optional().nullable(),
  fat_grams: z.coerce.number().min(0).max(500).optional().nullable(),
  fiber_grams: z.coerce.number().min(0).max(200).optional().nullable(),
  sodium_mg: z.coerce.number().min(0).max(20000).optional().nullable(),
});

interface NutritionLogDrawerProps {
  log: NutritionLog | null;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: NutritionFormData) => Promise<void>;
  mode?: 'view' | 'edit';
  isReadOnly?: boolean;
}

export function NutritionLogDrawer({
  log,
  isOpen,
  onClose,
  onSubmit,
  mode = 'view',
  isReadOnly = false,
}: NutritionLogDrawerProps) {
  const { t } = useTranslation();
  const isEditMode = mode === 'edit' && !isReadOnly;

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<NutritionFormData>({
    resolver: zodResolver(nutritionSchema),
    defaultValues: {
      date: new Date().toISOString().split('T')[0],
      source: 'Manual',
      calories: 0,
      protein_grams: 0,
      carbs_grams: 0,
      fat_grams: 0,
      fiber_grams: 0,
      sodium_mg: 0,
    },
  });

  useEffect(() => {
    if (log) {
      reset({
        date: log.date.split('T')[0],
        source: log.source,
        calories: log.calories,
        protein_grams: log.protein_grams,
        carbs_grams: log.carbs_grams,
        fat_grams: log.fat_grams,
        fiber_grams: log.fiber_grams,
        sodium_mg: log.sodium_mg,
      });
    } else {
      reset({
        date: new Date().toISOString().split('T')[0],
        source: 'Manual',
        calories: 0,
        protein_grams: 0,
        carbs_grams: 0,
        fat_grams: 0,
        fiber_grams: 0,
        sodium_mg: 0,
      });
    }
  }, [log, reset, isOpen]);

  const handleFormSubmit = async (data: NutritionFormData) => {
    if (isReadOnly) return;
    await onSubmit(data);
  };

  if (!log && !isEditMode) return null;

  return (
    <PremiumDrawer
      isOpen={isOpen}
      onClose={onClose}
      title={isEditMode
        ? (log ? t('body.nutrition.edit_title') : t('body.nutrition.register_title'))
        : t('body.nutrition.record_details')}
      subtitle={log ? formatDate(log.date) : undefined}
      icon={isEditMode ? <Pencil className="text-amber-400" size={24} /> : <Flame className="text-[color:var(--color-tertiary)]" size={24} />}
    >
      {isReadOnly && (
        <div className="mb-6 rounded-2xl border border-amber-500/20 bg-amber-500/5 px-4 py-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-amber-200">
          Demo Read-Only
        </div>
      )}

      {isEditMode ? (
        <form onSubmit={(e) => { void handleSubmit(handleFormSubmit)(e); }} className="space-y-8">
          <FormField label={t('body.nutrition.date')} id="nutrition-date" error={errors.date?.message}>
            <Input
              id="nutrition-date"
              type="date"
              disabled={isReadOnly}
              {...register('date')}
              className="h-14 rounded-2xl font-bold"
            />
          </FormField>

          <div className="bg-[color:var(--color-surface-container)] p-6 rounded-3xl border border-[color:var(--color-outline-variant)] shadow-inner">
            <FormField label={t('body.nutrition.calories')} id="calories" error={errors.calories?.message}>
              <Input
                id="calories"
                type="number"
                step="any"
                placeholder="500"
                disabled={isReadOnly}
                {...register('calories')}
                className="h-20 rounded-2xl text-4xl font-semibold"
              />
            </FormField>
          </div>

          <div className="space-y-6">
            <div className="flex items-center gap-2 pb-2 border-b border-[color:var(--color-outline-variant)]">
              <History className="text-[color:var(--color-primary)]" size={18} />
              <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider">{t('body.nutrition.macros_breakdown')}</h3>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <FormField label={t('body.nutrition.protein')} id="protein_grams" icon={<Beef size={14} className="text-text-secondary" />} error={errors.protein_grams?.message}>
                <Input id="protein_grams" type="number" step="any" disabled={isReadOnly} {...register('protein_grams')} className="h-14 rounded-2xl font-bold" />
              </FormField>
              <FormField label={t('body.nutrition.carbs')} id="carbs_grams" icon={<Wheat size={14} className="text-text-secondary" />} error={errors.carbs_grams?.message}>
                <Input id="carbs_grams" type="number" step="any" disabled={isReadOnly} {...register('carbs_grams')} className="h-14 rounded-2xl font-bold" />
              </FormField>
              <FormField label={t('body.nutrition.fat')} id="fat_grams" icon={<Droplets size={14} className="text-text-secondary" />} error={errors.fat_grams?.message}>
                <Input id="fat_grams" type="number" step="any" disabled={isReadOnly} {...register('fat_grams')} className="h-14 rounded-2xl font-bold" />
              </FormField>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField label={t('body.nutrition.fiber')} id="fiber_grams" error={errors.fiber_grams?.message}>
                <Input id="fiber_grams" type="number" step="any" disabled={isReadOnly} {...register('fiber_grams')} className="h-14 rounded-2xl font-bold" />
              </FormField>
              <FormField label={t('body.nutrition.sodium')} id="sodium_mg" error={errors.sodium_mg?.message}>
                <Input id="sodium_mg" type="number" step="any" disabled={isReadOnly} {...register('sodium_mg')} className="h-14 rounded-2xl font-bold" />
              </FormField>
            </div>
          </div>

          <Button fullWidth type="submit" isLoading={isSubmitting} disabled={isReadOnly} className="btn-premium h-16">
            <Save size={20} strokeWidth={3} />
            {t('common.save')}
          </Button>
        </form>
      ) : log && (
        <div className="space-y-8">
          <div className="bg-[color:var(--color-surface-container)] p-6 rounded-3xl border border-[color:var(--color-outline-variant)] flex items-center justify-between">
            <div>
              <p className="text-xs text-text-muted mb-1 font-bold uppercase tracking-wider">{t('body.nutrition.calories')}</p>
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-semibold text-text-primary">{log.calories}</span>
                <span className="text-xl text-text-muted font-bold">kcal</span>
              </div>
            </div>
            <div className="bg-[color:var(--color-tertiary)]/10 p-4 rounded-2xl shadow-[0_0_15px_rgba(249,115,22,0.1)]">
              <Flame className="text-[color:var(--color-tertiary)]" size={32} />
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-[color:var(--color-outline-variant)]">
              <History className="text-[color:var(--color-primary)]" size={18} />
              <h3 className="text-xs font-semibold text-text-primary uppercase tracking-[0.05em]">
                {t('body.nutrition.macros_breakdown')}
              </h3>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="bg-[color:var(--color-surface-container)] p-4 rounded-2xl border border-[color:var(--color-outline-variant)] space-y-2">
                <div className="flex items-center gap-2 text-[color:var(--color-error)]">
                  <Beef size={14} />
                  <span className="text-[10px] font-semibold uppercase tracking-wider">{t('body.nutrition.protein')}</span>
                </div>
                <p className="text-xl font-semibold text-text-primary">{log.protein_grams}g</p>
              </div>

              <div className="bg-[color:var(--color-surface-container)] p-4 rounded-2xl border border-[color:var(--color-outline-variant)] space-y-2">
                <div className="flex items-center gap-2 text-blue-400">
                  <Wheat size={14} />
                  <span className="text-[10px] font-semibold uppercase tracking-wider">{t('body.nutrition.carbs')}</span>
                </div>
                <p className="text-xl font-semibold text-text-primary">{log.carbs_grams}g</p>
              </div>

              <div className="bg-[color:var(--color-surface-container)] p-4 rounded-2xl border border-[color:var(--color-outline-variant)] space-y-2">
                <div className="flex items-center gap-2 text-[color:var(--color-secondary)]">
                  <Droplets size={14} />
                  <span className="text-[10px] font-semibold uppercase tracking-wider">{t('body.nutrition.fat')}</span>
                </div>
                <p className="text-xl font-semibold text-text-primary">{log.fat_grams}g</p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-[color:var(--color-surface-container)] p-4 rounded-2xl border border-[color:var(--color-outline-variant)] space-y-2">
                <div className="flex items-center gap-2 text-violet-400">
                  <span className="text-[10px] font-semibold uppercase tracking-wider">{t('body.nutrition.fiber')}</span>
                </div>
                <p className="text-xl font-semibold text-text-primary">{log.fiber_grams}g</p>
              </div>

              <div className="bg-[color:var(--color-surface-container)] p-4 rounded-2xl border border-[color:var(--color-outline-variant)] space-y-2">
                <div className="flex items-center gap-2 text-cyan-400">
                  <span className="text-[10px] font-semibold uppercase tracking-wider">{t('body.nutrition.sodium')}</span>
                </div>
                <p className="text-xl font-semibold text-text-primary">{log.sodium_mg}mg</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4 p-5 bg-[color:var(--color-surface-container)] rounded-2xl text-sm border border-[color:var(--color-outline-variant)]">
            <Calendar className="text-text-muted" size={20} />
            <span className="text-text-secondary font-bold capitalize">{formatDate(log.date)}</span>
          </div>
        </div>
      )}
    </PremiumDrawer>
  );
}
