import { zodResolver } from '@hookform/resolvers/zod';
import { Flame, Beef, Wheat, Droplets, Pencil, Save, History, Calendar } from 'lucide-react';
import { useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { z } from 'zod';

import { Button } from '../../../shared/components/ui/Button';
import { DateInput } from '../../../shared/components/ui/DateInput';
import { Input } from '../../../shared/components/ui/Input';
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

  const { register, handleSubmit, reset, control, formState: { errors, isSubmitting } } = useForm<NutritionFormData>({
    resolver: zodResolver(nutritionSchema),
    defaultValues: {
      date: new Date().toISOString().split('T')[0],
      source: 'Manual',
      calories: 0,
      protein_grams: 0,
      carbs_grams: 0,
      fat_grams: 0,
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
      icon={isEditMode ? <Pencil className="text-amber-400" size={24} /> : <Flame className="text-orange-500" size={24} />}
    >
      {isReadOnly && (
        <div className="mb-6 rounded-2xl border border-amber-500/20 bg-amber-500/5 px-4 py-3 text-[10px] font-black uppercase tracking-[0.2em] text-amber-200">
          Demo Read-Only
        </div>
      )}

      {isEditMode ? (
        <form onSubmit={(e) => { void handleSubmit(handleFormSubmit)(e); }} className="space-y-6">
          <div className="space-y-4">
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
              step="any"
              placeholder="Ex: 500" 
              disabled={isReadOnly}
              error={errors.calories?.message}
              {...register('calories')}
            />
            
            <div className="grid grid-cols-3 gap-4">
              <Input 
                id="protein_grams"
                label={t('body.nutrition.protein')} 
                type="number" 
                step="any"
                disabled={isReadOnly}
                error={errors.protein_grams?.message}
                {...register('protein_grams')}
              />
              <Input 
                id="carbs_grams"
                label={t('body.nutrition.carbs')} 
                type="number" 
                step="any"
                disabled={isReadOnly}
                error={errors.carbs_grams?.message}
                {...register('carbs_grams')}
              />
              <Input 
                id="fat_grams"
                label={t('body.nutrition.fat')} 
                type="number" 
                step="any"
                disabled={isReadOnly}
                error={errors.fat_grams?.message}
                {...register('fat_grams')}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                id="fiber_grams"
                label={t('body.nutrition.fiber')}
                type="number"
                step="any"
                disabled={isReadOnly}
                error={errors.fiber_grams?.message}
                {...register('fiber_grams')}
              />
              <Input
                id="sodium_mg"
                label={t('body.nutrition.sodium')}
                type="number"
                step="any"
                disabled={isReadOnly}
                error={errors.sodium_mg?.message}
                {...register('sodium_mg')}
              />
            </div>
          </div>

          <div className="pt-6 flex gap-4">
            <Button 
              fullWidth 
              variant="secondary" 
              type="button" 
              onClick={onClose}
              className="rounded-2xl"
            >
              {t('common.cancel')}
            </Button>
            <Button 
              fullWidth 
              variant="primary" 
              type="submit" 
              isLoading={isSubmitting}
              disabled={isReadOnly}
              className="shadow-orange rounded-2xl"
            >
              <Save size={18} className="mr-2" />
              {t('common.save')}
            </Button>
          </div>
        </form>
      ) : log && (
        <div className="space-y-8">
          {/* Summary Card */}
          <div className="bg-white/5 p-6 rounded-3xl border border-white/10 flex items-center justify-between">
            <div>
              <p className="text-xs text-zinc-500 mb-1 font-bold uppercase tracking-wider">{t('body.nutrition.calories')}</p>
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-black text-white">{log.calories}</span>
                <span className="text-xl text-zinc-500 font-bold">kcal</span>
              </div>
            </div>
            <div className="bg-orange-500/10 p-4 rounded-2xl shadow-[0_0_15px_rgba(249,115,22,0.1)]">
              <Flame className="text-orange-500" size={32} />
            </div>
          </div>

          {/* Macros Breakdown */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-white/5">
              <History className="text-indigo-400" size={18} />
              <h3 className="text-xs font-black text-white uppercase tracking-widest">
                {t('body.nutrition.macros_breakdown')}
              </h3>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white/5 p-4 rounded-2xl border border-white/5 space-y-2">
                <div className="flex items-center gap-2 text-red-400">
                  <Beef size={14} />
                  <span className="text-[10px] font-black uppercase tracking-wider">{t('body.nutrition.protein')}</span>
                </div>
                <p className="text-xl font-black text-white">{log.protein_grams}g</p>
              </div>
              
              <div className="bg-white/5 p-4 rounded-2xl border border-white/5 space-y-2">
                <div className="flex items-center gap-2 text-blue-400">
                  <Wheat size={14} />
                  <span className="text-[10px] font-black uppercase tracking-wider">{t('body.nutrition.carbs')}</span>
                </div>
                <p className="text-xl font-black text-white">{log.carbs_grams}g</p>
              </div>

              <div className="bg-white/5 p-4 rounded-2xl border border-white/5 space-y-2">
                <div className="flex items-center gap-2 text-emerald-400">
                  <Droplets size={14} />
                  <span className="text-[10px] font-black uppercase tracking-wider">{t('body.nutrition.fat')}</span>
                </div>
                <p className="text-xl font-black text-white">{log.fat_grams}g</p>
              </div>
            </div>
          </div>

          {/* Date Info */}
          <div className="flex items-center gap-4 p-5 bg-white/5 rounded-2xl text-sm border border-white/5">
            <Calendar className="text-zinc-500" size={20} />
            <span className="text-zinc-300 font-bold capitalize">{formatDate(log.date)}</span>
          </div>
        </div>
      )}
    </PremiumDrawer>
  );
}
