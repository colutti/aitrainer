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

const weightSchema = z.object({
  date: z.string().optional(),
  weight_kg: z.coerce.number().min(20).max(300),
  body_fat_pct: z.coerce.number().min(2).max(70),
  muscle_mass_kg: z.preprocess(
    (val) => (val === '' || val === undefined || val === null ? null : Number(val)),
    z.number().min(10).max(150).nullable().optional()
  ),
  visceral_fat: z.preprocess(
    (val) => (val === '' || val === undefined || val === null ? null : Number(val)),
    z.number().min(1).max(30).nullable().optional()
  ),
  body_water_pct: z.preprocess(
    (val) => (val === '' || val === undefined || val === null ? null : Number(val)),
    z.number().min(20).max(90).nullable().optional()
  ),
  bone_mass_kg: z.preprocess(
    (val) => (val === '' || val === undefined || val === null ? null : Number(val)),
    z.number().min(1).max(15).nullable().optional()
  ),
  bmr: z.preprocess(
    (val) => (val === '' || val === undefined || val === null ? null : Number(val)),
    z.number().min(500).max(5000).nullable().optional()
  ),
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
    // Format date to YYYY-MM-DD for backend
    const formattedData = {
      ...data,
      date: data.date ? data.date.split('T')[0] : new Date().toISOString().split('T')[0]
    };
    await onSubmit(formattedData as WeightLogFormData);
  };

  useEffect(() => {
    if (log) {
      reset({
        date: log.date,
        weight_kg: log.weight_kg,
        body_fat_pct: log.body_fat_pct ?? 0,
        muscle_mass_kg: log.muscle_mass_kg,
        visceral_fat: log.visceral_fat,
        body_water_pct: log.body_water_pct,
        bone_mass_kg: log.bone_mass_kg,
        bmr: log.bmr,
        notes: log.notes,
      });
    } else {
      reset({ weight_kg: 0, body_fat_pct: 0, date: new Date().toISOString() });
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
        <input type="hidden" {...register('date')} />
        
        {/* PRIMARY METRIC */}
        <div className="bg-white/5 p-6 rounded-3xl border border-white/10 shadow-inner">
          <FormField label={t('body.weight.weight')} id="weight-kg" error={errors.weight_kg?.message}>
            <div className="relative">
              <Scale className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500" size={24} />
              <Input
                id="weight-kg"
                data-testid="weight-kg"
                type="number"
                step="0.1"
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
              <Input id="body-fat-pct" data-testid="body-fat-pct" type="number" step="0.1" disabled={isReadOnly} {...register('body_fat_pct')} placeholder="%" className="h-14 rounded-2xl font-bold" />
            </FormField>
            
            <FormField label={t('body.weight.muscle_mass')} id="muscle-mass-kg" icon={<Bone size={14} className="text-emerald-400" />} error={errors.muscle_mass_kg?.message}>
              <Input id="muscle-mass-kg" type="number" step="0.1" disabled={isReadOnly} {...register('muscle_mass_kg')} placeholder="kg" className="h-14 rounded-2xl font-bold" />
            </FormField>

            <FormField label={t('body.weight.visceral_fat')} id="visceral-fat" icon={<Ruler size={14} className="text-blue-400" />} error={errors.visceral_fat?.message}>
              <Input id="visceral-fat" type="number" step="1" disabled={isReadOnly} {...register('visceral_fat')} placeholder="1-20" className="h-14 rounded-2xl font-bold" />
            </FormField>

            <FormField label={t('body.weight.water')} id="body-water-pct" icon={<Droplets size={14} className="text-cyan-400" />} error={errors.body_water_pct?.message}>
              <Input id="body-water-pct" type="number" step="0.1" disabled={isReadOnly} {...register('body_water_pct')} placeholder="%" className="h-14 rounded-2xl font-bold" />
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
