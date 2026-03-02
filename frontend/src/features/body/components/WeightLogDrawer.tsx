import { X, Scale, Activity, Ruler, FileText, Droplets, Zap, Target, Bone, Flame, Pencil, Save } from 'lucide-react';
import { type UseFormRegister, type Control, type FieldErrors, type UseFormHandleSubmit, Controller } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { Button } from '../../../shared/components/ui/Button';
import { DateInput } from '../../../shared/components/ui/DateInput';
import { Input } from '../../../shared/components/ui/Input';
import type { WeightLog, WeightLogFormData } from '../../../shared/types/body';
import { cn } from '../../../shared/utils/cn';
import { formatDate } from '../../../shared/utils/format-date';

interface WeightLogDrawerProps {
  log: WeightLog | null;
  isOpen: boolean;
  onClose: () => void;
  mode?: 'view' | 'edit';
  // Form props (only used in edit mode)
  register?: UseFormRegister<WeightLogFormData>;
  control?: Control<WeightLogFormData>;
  errors?: FieldErrors<WeightLogFormData>;
  isSaving?: boolean;
  handleSubmit?: UseFormHandleSubmit<WeightLogFormData>;
  onSubmit?: (data: WeightLogFormData) => Promise<void>;
  onCancelEdit?: () => void;
}

/**
 * Drawer component to display detailed weight log information OR the entry form
 * Slides in from the right side of the screen
 */
export function WeightLogDrawer({ 
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
  onCancelEdit
}: WeightLogDrawerProps) {
  const { t } = useTranslation();
  
  const isEditMode = mode === 'edit';

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
              <Scale className="text-gradient-start" size={24} />
            )}
            <div>
              <h2 className="text-xl font-bold text-text-primary">
                {isEditMode 
                  ? (log ? t('body.weight.edit_title') : t('body.weight.register_title'))
                  : t('body.weight.record_details')}
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

        {/* Content */}
        <div className="p-6">
          {isEditMode && handleSubmit && onSubmit && register && control && errors ? (
            <form onSubmit={(e) => { void handleSubmit(onSubmit)(e); }} className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-text-secondary uppercase tracking-wider">{t('body.weight.composition_title')}</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
                </div>
              </div>

              <Input 
                id="notes"
                label={t('body.weight.notes')} 
                type="text" 
                placeholder={t('body.weight.notes_placeholder')}
                error={errors.notes?.message}
                {...register('notes')}
              />

              <div className="pt-6 border-t border-border">
                <h3 className="text-sm font-bold text-text-secondary uppercase tracking-wider mb-4">{t('body.weight.measurements_title')}</h3>
                <div className="grid grid-cols-2 gap-4">
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
                  className="shadow-orange"
                >
                  <Save size={18} className="mr-2" />
                  {t('body.weight.save')}
                </Button>
              </div>
            </form>
          ) : log && (
            <div className="space-y-8">
              {/* Main Weight Display */}
              <div className="flex items-center justify-between bg-zinc-900/50 p-6 rounded-2xl border border-white/5">
                <div>
                  <p className="text-sm text-text-muted mb-1 font-medium uppercase tracking-wider">{t('body.weight.registered_weight')}</p>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-black text-white">{log.weight_kg.toFixed(2)}</span>
                    <span className="text-xl text-text-secondary font-medium">kg</span>
                  </div>
                </div>
                {log.trend_weight !== undefined && (
                  <div className="text-right">
                    <p className="text-xs text-text-muted mb-1 font-medium uppercase tracking-wider">{t('body.weight.trend')}</p>
                    <div className={cn(
                      "text-lg font-bold flex items-center justify-end gap-1",
                      log.weight_kg > (log.trend_weight || 0) ? "text-red-400" : "text-emerald-400"
                    )}>
                        {log.weight_kg > (log.trend_weight || 0) ? '▲' : '▼'}
                        {Math.abs(log.weight_kg - (log.trend_weight || 0)).toFixed(2)}kg
                    </div>
                  </div>
                )}
              </div>

              {/* Body Composition Grid */}
              {(log.body_fat_pct != null || log.muscle_mass_pct != null || log.muscle_mass_kg != null || log.body_water_pct != null || log.bone_mass_kg != null || log.visceral_fat != null || log.bmr != null || log.bmi != null) && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 pb-2 border-b border-white/5">
                    <Activity className="text-blue-400" size={18} />
                    <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider">
                      {t('body.weight.composition_title')}
                    </h3>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    {log.body_fat_pct != null && (
                      <div className="bg-zinc-900/30 p-3 rounded-xl border border-white/5">
                        <div className="flex items-center gap-2 mb-1">
                          <Target size={14} className="text-orange-400" />
                          <p className="text-[10px] text-text-muted font-bold uppercase">{t('body.weight.body_fat').split(' ')[0]}</p>
                        </div>
                        <p className="text-xl font-bold text-text-primary">{log.body_fat_pct}%</p>
                      </div>
                    )}
                    
                    {(log.muscle_mass_pct != null || log.muscle_mass_kg != null) && (
                      <div className="bg-zinc-900/30 p-3 rounded-xl border border-white/5">
                        <div className="flex items-center gap-2 mb-1">
                          <Zap size={14} className="text-yellow-400" />
                          <p className="text-[10px] text-text-muted font-bold uppercase">{t('body.weight.muscle_mass')}</p>
                        </div>
                        {log.muscle_mass_kg != null ? (
                          <p className="text-xl font-bold text-text-primary">{log.muscle_mass_kg}kg</p>
                        ) : (
                          <p className="text-xl font-bold text-text-primary">{log.muscle_mass_pct}%</p>
                        )}
                      </div>
                    )}

                    {log.body_water_pct != null && (
                      <div className="bg-zinc-900/30 p-3 rounded-xl border border-white/5">
                        <div className="flex items-center gap-2 mb-1">
                          <Droplets size={14} className="text-blue-400" />
                          <p className="text-[10px] text-text-muted font-bold uppercase">{t('body.weight.body_water')}</p>
                        </div>
                        <p className="text-xl font-bold text-text-primary">{log.body_water_pct}%</p>
                      </div>
                    )}

                    {log.bone_mass_kg != null && (
                      <div className="bg-zinc-900/30 p-3 rounded-xl border border-white/5">
                        <div className="flex items-center gap-2 mb-1">
                          <Bone size={14} className="text-zinc-400" />
                          <p className="text-[10px] text-text-muted font-bold uppercase">{t('body.weight.bone_mass')}</p>
                        </div>
                        <p className="text-xl font-bold text-text-primary">{log.bone_mass_kg}kg</p>
                      </div>
                    )}

                    {log.visceral_fat != null && (
                      <div className="bg-zinc-900/30 p-3 rounded-xl border border-white/5">
                        <div className="flex items-center gap-2 mb-1">
                          <Activity size={14} className="text-red-400" />
                          <p className="text-[10px] text-text-muted font-bold uppercase">{t('body.weight.visceral_fat')}</p>
                        </div>
                        <p className="text-xl font-bold text-text-primary">{log.visceral_fat}</p>
                      </div>
                    )}

                    {log.bmr != null && (
                      <div className="bg-zinc-900/30 p-3 rounded-xl border border-white/5">
                        <div className="flex items-center gap-2 mb-1">
                            <Flame className="text-orange-500" size={14} />
                            <p className="text-[10px] text-text-muted font-bold uppercase">{t('body.metabolism.metabolic_rate')}</p>
                        </div>
                        <p className="text-xl font-bold text-text-primary">{log.bmr} kcal</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Measurements Grid - Always visible in View Mode */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 pb-2 border-b border-white/5">
                  <Ruler className="text-emerald-400" size={18} />
                  <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider">
                    {t('body.weight.measurements_short_title')}
                  </h3>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {[
                      { label: t('body.weight.neck'), value: log.neck_cm },
                      { label: t('body.weight.chest'), value: log.chest_cm },
                      { label: t('body.weight.waist'), value: log.waist_cm },
                      { label: t('body.weight.hips'), value: log.hips_cm },
                      { label: t('body.weight.bicep_r'), value: log.bicep_r_cm },
                      { label: t('body.weight.bicep_l'), value: log.bicep_l_cm },
                      { label: t('body.weight.thigh_r'), value: log.thigh_r_cm },
                      { label: t('body.weight.thigh_l'), value: log.thigh_l_cm },
                      { label: t('body.weight.calf_r'), value: log.calf_r_cm },
                      { label: t('body.weight.calf_l'), value: log.calf_l_cm },
                    ].map((item) => (
                      <div key={item.label} className={cn(
                        "px-3 py-2 rounded-lg border flex justify-between items-center transition-colors",
                        item.value 
                          ? "bg-zinc-900/30 border-white/5" 
                          : "bg-zinc-900/10 border-white/5 opacity-50"
                      )}>
                        <span className="text-xs text-text-muted">{item.label}</span>
                        <span className={cn(
                          "font-mono font-bold",
                          item.value ? "text-text-primary" : "text-text-muted/50"
                        )}>
                          {item.value ?? '-'}
                        </span>
                      </div>
                    ))}
                </div>
              </div>

              {/* Notes */}
              {log.notes && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 pb-2 border-b border-white/5">
                    <FileText className="text-purple-400" size={18} />
                    <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider">
                      {t('body.weight.notes')}
                    </h3>
                  </div>
                  <div className="bg-zinc-900/30 p-4 rounded-xl border border-white/5 text-sm text-text-secondary italic leading-relaxed">
                    "{log.notes}"
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
