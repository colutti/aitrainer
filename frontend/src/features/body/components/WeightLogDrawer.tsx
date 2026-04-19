import { zodResolver } from '@hookform/resolvers/zod';
import { Scale, Ruler, FileText, Droplets, Target, Bone, Flame, Save } from 'lucide-react';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { z } from 'zod';

import { Button } from '../../../shared/components/ui/Button';
import { Input } from '../../../shared/components/ui/Input';
import { FormField } from '../../../shared/components/ui/premium/FormField';
import { PremiumDrawer } from '../../../shared/components/ui/premium/PremiumDrawer';
import type { WeightLog, WeightLogFormData } from '../../../shared/types/body';

const optionalNumber = (min: number, max: number) => z.preprocess(
  (val) => (val === '' || val === undefined || val === null ? undefined : Number(val)),
  z.number().min(min).max(max).optional().nullable(),
);

const weightSchema = z.object({
  date: z.string().min(1),
  weight_kg: z.coerce.number().min(20).max(300),
  body_fat_pct: z.coerce.number().min(2).max(70),
  muscle_mass_pct: optionalNumber(2, 100),
  muscle_mass_kg: optionalNumber(10, 150),
  visceral_fat: optionalNumber(1, 50),
  body_water_pct: optionalNumber(2, 100),
  bone_mass_kg: optionalNumber(0, 20),
  bmr: optionalNumber(500, 5000),
  neck_cm: optionalNumber(20, 100),
  chest_cm: optionalNumber(40, 200),
  waist_cm: optionalNumber(40, 200),
  hips_cm: optionalNumber(40, 200),
  bicep_r_cm: optionalNumber(10, 100),
  bicep_l_cm: optionalNumber(10, 100),
  thigh_r_cm: optionalNumber(20, 150),
  thigh_l_cm: optionalNumber(20, 150),
  calf_r_cm: optionalNumber(10, 100),
  calf_l_cm: optionalNumber(10, 100),
  notes: z.string().max(500).optional().nullable(),
});

interface WeightLogDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: WeightLogFormData) => Promise<void>;
  isReadOnly?: boolean;
  log?: WeightLog | null;
}

export function WeightLogDrawer({ isOpen, onClose, onSubmit, isReadOnly = false, log }: WeightLogDrawerProps) {
  const { t } = useTranslation();
  
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<WeightLogFormData>({
    resolver: zodResolver(weightSchema),
  });

  const handleFormSubmit = async (data: WeightLogFormData) => {
    if (isReadOnly) {
      return;
    }
    const formattedData = {
      ...data,
      date: data.date ? data.date.split('T')[0] : new Date().toISOString().split('T')[0],
    };
    await onSubmit(formattedData as WeightLogFormData);
  };

  useEffect(() => {
    if (log) {
      reset({
        date: log.date.split('T')[0],
        weight_kg: log.weight_kg,
        body_fat_pct: log.body_fat_pct ?? 0,
        muscle_mass_pct: log.muscle_mass_pct,
        muscle_mass_kg: log.muscle_mass_kg,
        visceral_fat: log.visceral_fat,
        body_water_pct: log.body_water_pct,
        bone_mass_kg: log.bone_mass_kg,
        bmr: log.bmr,
        neck_cm: log.neck_cm,
        chest_cm: log.chest_cm,
        waist_cm: log.waist_cm,
        hips_cm: log.hips_cm,
        bicep_r_cm: log.bicep_r_cm,
        bicep_l_cm: log.bicep_l_cm,
        thigh_r_cm: log.thigh_r_cm,
        thigh_l_cm: log.thigh_l_cm,
        calf_r_cm: log.calf_r_cm,
        calf_l_cm: log.calf_l_cm,
        notes: log.notes,
      });
    } else {
      reset({ weight_kg: 0, body_fat_pct: 0, date: new Date().toISOString().split('T')[0] });
    }
  }, [log, reset, isOpen]);

  return (
    <PremiumDrawer
      isOpen={isOpen}
      onClose={onClose}
      title={log ? t('body.weight.record_details') : t('body.weight.register_weight')}
      subtitle={log ? log.date : t('body.weight_subtitle')}
      icon={<Scale size={24} />}
    >
      {isReadOnly && (
        <div className="mb-6 rounded-2xl border border-amber-500/20 bg-amber-500/5 px-4 py-3 text-[10px] font-black uppercase tracking-[0.2em] text-amber-200">
          Demo Read-Only
        </div>
      )}
      <form onSubmit={(e) => { void handleSubmit(handleFormSubmit)(e); }} className="space-y-8">
        <FormField label={t('body.nutrition.date')} id="weight-date" error={errors.date?.message}>
          <Input
            id="weight-date"
            type="date"
            disabled={isReadOnly}
            {...register('date')}
            className="h-14 rounded-2xl font-bold"
          />
        </FormField>
        
        {/* PRIMARY METRIC */}
        <div className="bg-white/5 p-6 rounded-3xl border border-white/10 shadow-inner">
          <FormField label={t('body.weight.weight')} id="weight-kg" error={errors.weight_kg?.message}>
            <div className="relative">
              <Scale className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500" size={24} />
              <Input
                id="weight-kg"
                data-testid="weight-kg"
                type="number"
                step="any"
                disabled={isReadOnly}
                {...register('weight_kg')}
                placeholder="0.0"
                className="pl-14 h-20 text-4xl font-black bg-transparent border-transparent focus:border-white/10 rounded-2xl"
              />
              <span className="absolute right-6 top-1/2 -translate-y-1/2 text-xl font-bold text-zinc-500 uppercase">kg</span>
            </div>
          </FormField>
        </div>

        {/* COMPOSITION GRID */}
        <div className="space-y-6">
          <div className="flex items-center gap-2 pb-2 border-b border-white/5">
            <Target size={18} className="text-indigo-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">{t('body.weight.composition_title')}</h3>
          </div>
          
          <div className="grid grid-cols-2 gap-6">
            <FormField label={t('body.weight.body_fat')} id="body-fat-pct" icon={<Flame size={14} className="text-orange-400" />} error={errors.body_fat_pct?.message}>
              <Input id="body-fat-pct" data-testid="body-fat-pct" type="number" step="any" disabled={isReadOnly} {...register('body_fat_pct')} placeholder="%" className="h-14 rounded-2xl font-bold" />
            </FormField>

            <FormField label={`${t('body.weight.muscle_mass')} (%)`} id="muscle-mass-pct" icon={<Target size={14} className="text-violet-400" />} error={errors.muscle_mass_pct?.message}>
              <Input id="muscle-mass-pct" type="number" step="any" disabled={isReadOnly} {...register('muscle_mass_pct')} placeholder="%" className="h-14 rounded-2xl font-bold" />
            </FormField>
            
            <FormField label={t('body.weight.muscle_mass')} id="muscle-mass-kg" icon={<Bone size={14} className="text-emerald-400" />} error={errors.muscle_mass_kg?.message}>
              <Input id="muscle-mass-kg" type="number" step="any" disabled={isReadOnly} {...register('muscle_mass_kg')} placeholder="kg" className="h-14 rounded-2xl font-bold" />
            </FormField>

            <FormField label={t('body.weight.visceral_fat')} id="visceral-fat" icon={<Ruler size={14} className="text-blue-400" />} error={errors.visceral_fat?.message}>
              <Input id="visceral-fat" type="number" step="any" disabled={isReadOnly} {...register('visceral_fat')} placeholder="1-20" className="h-14 rounded-2xl font-bold" />
            </FormField>

            <FormField label={t('body.weight.body_water')} id="body-water-pct" icon={<Droplets size={14} className="text-cyan-400" />} error={errors.body_water_pct?.message}>
              <Input id="body-water-pct" type="number" step="any" disabled={isReadOnly} {...register('body_water_pct')} placeholder="%" className="h-14 rounded-2xl font-bold" />
            </FormField>

            <FormField label={t('body.weight.bone_mass')} id="bone-mass-kg" icon={<Bone size={14} className="text-slate-400" />} error={errors.bone_mass_kg?.message}>
              <Input id="bone-mass-kg" type="number" step="any" disabled={isReadOnly} {...register('bone_mass_kg')} placeholder="kg" className="h-14 rounded-2xl font-bold" />
            </FormField>

            <FormField label={t('body.weight.bmr')} id="bmr" icon={<Flame size={14} className="text-rose-400" />} error={errors.bmr?.message}>
              <Input id="bmr" type="number" step="1" disabled={isReadOnly} {...register('bmr')} placeholder="kcal" className="h-14 rounded-2xl font-bold" />
            </FormField>
          </div>
        </div>

        {/* BODY MEASUREMENTS */}
        <div className="space-y-6">
          <div className="flex items-center gap-2 pb-2 border-b border-white/5">
            <Ruler size={18} className="text-indigo-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">{t('body.weight.measurements_title')}</h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormField label={t('body.weight.neck')} id="neck-cm" error={errors.neck_cm?.message}>
              <Input id="neck-cm" type="number" step="any" disabled={isReadOnly} {...register('neck_cm')} className="h-12 rounded-2xl font-bold" />
            </FormField>
            <FormField label={t('body.weight.chest')} id="chest-cm" error={errors.chest_cm?.message}>
              <Input id="chest-cm" type="number" step="any" disabled={isReadOnly} {...register('chest_cm')} className="h-12 rounded-2xl font-bold" />
            </FormField>
            <FormField label={t('body.weight.waist')} id="waist-cm" error={errors.waist_cm?.message}>
              <Input id="waist-cm" type="number" step="any" disabled={isReadOnly} {...register('waist_cm')} className="h-12 rounded-2xl font-bold" />
            </FormField>
            <FormField label={t('body.weight.hips')} id="hips-cm" error={errors.hips_cm?.message}>
              <Input id="hips-cm" type="number" step="any" disabled={isReadOnly} {...register('hips_cm')} className="h-12 rounded-2xl font-bold" />
            </FormField>
            <FormField label={t('body.weight.bicep_r')} id="bicep-r-cm" error={errors.bicep_r_cm?.message}>
              <Input id="bicep-r-cm" type="number" step="any" disabled={isReadOnly} {...register('bicep_r_cm')} className="h-12 rounded-2xl font-bold" />
            </FormField>
            <FormField label={t('body.weight.bicep_l')} id="bicep-l-cm" error={errors.bicep_l_cm?.message}>
              <Input id="bicep-l-cm" type="number" step="any" disabled={isReadOnly} {...register('bicep_l_cm')} className="h-12 rounded-2xl font-bold" />
            </FormField>
            <FormField label={t('body.weight.thigh_r')} id="thigh-r-cm" error={errors.thigh_r_cm?.message}>
              <Input id="thigh-r-cm" type="number" step="any" disabled={isReadOnly} {...register('thigh_r_cm')} className="h-12 rounded-2xl font-bold" />
            </FormField>
            <FormField label={t('body.weight.thigh_l')} id="thigh-l-cm" error={errors.thigh_l_cm?.message}>
              <Input id="thigh-l-cm" type="number" step="any" disabled={isReadOnly} {...register('thigh_l_cm')} className="h-12 rounded-2xl font-bold" />
            </FormField>
            <FormField label={t('body.weight.calf_r')} id="calf-r-cm" error={errors.calf_r_cm?.message}>
              <Input id="calf-r-cm" type="number" step="any" disabled={isReadOnly} {...register('calf_r_cm')} className="h-12 rounded-2xl font-bold" />
            </FormField>
            <FormField label={t('body.weight.calf_l')} id="calf-l-cm" error={errors.calf_l_cm?.message}>
              <Input id="calf-l-cm" type="number" step="any" disabled={isReadOnly} {...register('calf_l_cm')} className="h-12 rounded-2xl font-bold" />
            </FormField>
          </div>
        </div>

        {/* NOTES */}
        <FormField label={t('body.weight.notes')} id="notes" icon={<FileText size={14} />} error={errors.notes?.message} optional>
          <textarea
            id="notes"
            {...register('notes')}
            disabled={isReadOnly}
            className="form-field w-full h-32 rounded-2xl p-4 text-sm font-medium resize-none custom-scrollbar"
            placeholder={t('body.weight.notes_placeholder')}
          />
        </FormField>

        {/* SUBMIT */}
        <Button 
        type="submit" 
        fullWidth 
        isLoading={isSubmitting}
        disabled={isReadOnly}
        className="btn-premium h-16"
      >
          <Save size={20} strokeWidth={3} />
          {t('common.save')}
        </Button>
      </form>
    </PremiumDrawer>
  );
}
