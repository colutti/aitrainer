import { X, Flame, Beef, Wheat, Droplet, Pencil, Save, History, Calendar } from 'lucide-react';
import { type UseFormRegister, type Control, type FieldErrors, type UseFormHandleSubmit, Controller } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { Button } from '../../../shared/components/ui/Button';
import { DateInput } from '../../../shared/components/ui/DateInput';
import { Input } from '../../../shared/components/ui/Input';
import { type NutritionLog, type NutritionFormData } from '../../../shared/types/nutrition';
import { cn } from '../../../shared/utils/cn';
import { formatDate } from '../../../shared/utils/format-date';

interface NutritionLogDrawerProps {
  log: NutritionLog | null;
  isOpen: boolean;
  onClose: () => void;
  mode?: 'view' | 'edit';
  isReadOnly?: boolean;
  // Form props (only used in edit mode)
  register?: UseFormRegister<NutritionFormData>;
  control?: Control<NutritionFormData>;
  errors?: FieldErrors<NutritionFormData>;
  isSaving?: boolean;
  handleSubmit?: UseFormHandleSubmit<NutritionFormData>;
  onSubmit?: (data: NutritionFormData) => Promise<void>;
  onCancelEdit?: () => void;
}

export function NutritionLogDrawer({
  log,
  isOpen,
  onClose,
  mode = 'view',
  register,
  control,
  errors,
  isSaving,
  handleSubmit,
  onSubmit,
  onCancelEdit,
  isReadOnly = false,
}: NutritionLogDrawerProps) {
  const { t } = useTranslation();
  const isEditMode = mode === 'edit' && !isReadOnly;
  const canEdit = mode === 'edit' && !isReadOnly;

  if (!log && !isEditMode) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className={cn(
          'fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity',
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        )}
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className={cn(
          'fixed right-0 top-0 h-full w-full md:w-[500px] bg-dark-card border-l border-border z-50',
          'transform transition-transform duration-300 ease-in-out overflow-y-auto',
          isOpen ? 'translate-x-0' : 'translate-x-full'
        )}
      >
        {/* Header */}
        <div className="sticky top-0 bg-dark-card/95 backdrop-blur-md border-b border-border p-6 flex items-center justify-between z-10">
          <div className="flex items-center gap-3">
            {isEditMode ? (
              <Pencil className="text-amber-400" size={24} />
            ) : (
              <Flame className="text-orange-500" size={24} />
            )}
            <div>
              <h2 className="text-xl font-bold text-text-primary">
                {isEditMode 
                  ? (log ? t('body.nutrition.edit_title') : t('body.nutrition.register_title'))
                  : t('body.nutrition.record_details')}
              </h2>
              {log && (
                <p className="text-sm text-text-secondary mt-0.5 capitalize">
                  {formatDate(log.date)}
                </p>
              )}
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="text-text-muted hover:text-text-primary"
          >
            <X size={20} />
          </Button>
        </div>
        {isReadOnly && (
          <div className="px-6 pb-4">
            <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 px-4 py-3 text-[10px] font-black uppercase tracking-[0.2em] text-amber-200">
              Demo Read-Only
            </div>
          </div>
        )}

        {/* Content */}
        <div className="p-6">
          {canEdit && handleSubmit && onSubmit && register && control && errors ? (
            <form onSubmit={(e) => { void handleSubmit(onSubmit)(e); }} className="space-y-6">
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
                  step="1"
                  placeholder="Ex: 500" 
                  error={errors.calories?.message}
                  {...register('calories', { valueAsNumber: true })}
                />
                
                <div className="grid grid-cols-3 gap-4">
                  <Input 
                    id="protein_grams"
                    label={t('body.nutrition.protein')} 
                    type="number" 
                    step="0.1"
                    error={errors.protein_grams?.message}
                    {...register('protein_grams', { valueAsNumber: true })}
                  />
                  <Input 
                    id="carbs_grams"
                    label={t('body.nutrition.carbs')} 
                    type="number" 
                    step="0.1"
                    error={errors.carbs_grams?.message}
                    {...register('carbs_grams', { valueAsNumber: true })}
                  />
                  <Input 
                    id="fat_grams"
                    label={t('body.nutrition.fat')} 
                    type="number" 
                    step="0.1"
                    error={errors.fat_grams?.message}
                    {...register('fat_grams', { valueAsNumber: true })}
                  />
                </div>
              </div>

              <div className="sticky bottom-0 pt-6 bg-dark-card/95 backdrop-blur-sm border-t border-border flex gap-4">
                <Button 
                  fullWidth 
                  variant="secondary" 
                  type="button" 
                  onClick={onCancelEdit ?? onClose}
                >
                  {t('common.cancel')}
                </Button>
                <Button 
                  fullWidth 
                  variant="primary" 
                  type="submit" 
                  isLoading={isSaving}
                  disabled={isReadOnly}
                  className="shadow-orange"
                >
                  <Save size={18} className="mr-2" />
                  {t('body.nutrition.save')}
                </Button>
              </div>
            </form>
          ) : log && (
            <div className="space-y-8">
              {/* Summary Card */}
              <div className="bg-zinc-900/50 p-6 rounded-2xl border border-white/5 flex items-center justify-between">
                <div>
                  <p className="text-sm text-text-muted mb-1 font-medium uppercase tracking-wider">{t('body.nutrition.calories')}</p>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-black text-white">{log.calories}</span>
                    <span className="text-xl text-text-secondary font-medium">kcal</span>
                  </div>
                </div>
                <div className="bg-orange-500/10 p-4 rounded-2xl">
                  <Flame className="text-orange-500" size={32} />
                </div>
              </div>

              {/* Macros Breakdown */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 pb-2 border-b border-white/5">
                  <History className="text-gradient-start" size={18} />
                  <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider">
                    {t('body.nutrition.macros_breakdown')}
                  </h3>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-zinc-900/30 p-4 rounded-xl border border-white/5 space-y-2">
                    <div className="flex items-center gap-2 text-red-400">
                      <Beef size={14} />
                      <span className="text-[10px] font-bold uppercase">{t('body.nutrition.protein')}</span>
                    </div>
                    <p className="text-xl font-bold">{log.protein_grams}g</p>
                  </div>
                  
                  <div className="bg-zinc-900/30 p-4 rounded-xl border border-white/5 space-y-2">
                    <div className="flex items-center gap-2 text-blue-400">
                      <Wheat size={14} />
                      <span className="text-[10px] font-bold uppercase">{t('body.nutrition.carbs')}</span>
                    </div>
                    <p className="text-xl font-bold">{log.carbs_grams}g</p>
                  </div>

                  <div className="bg-zinc-900/30 p-4 rounded-xl border border-white/5 space-y-2">
                    <div className="flex items-center gap-2 text-yellow-400">
                      <Droplet size={14} />
                      <span className="text-[10px] font-bold uppercase">{t('body.nutrition.fat')}</span>
                    </div>
                    <p className="text-xl font-bold">{log.fat_grams}g</p>
                  </div>
                </div>
              </div>

              {/* Date Info */}
              <div className="flex items-center gap-4 p-4 bg-white/5 rounded-xl text-sm border border-white/5">
                <Calendar className="text-text-muted" size={20} />
                <span className="text-text-secondary capitalize">{formatDate(log.date)}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
