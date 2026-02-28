import { zodResolver } from '@hookform/resolvers/zod';
import { useState, useCallback, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { z } from 'zod';

import { useNotificationStore } from '../../../shared/hooks/useNotification';
import type { WeightLog, BodyCompositionStats } from '../../../shared/types/body';
import { bodyApi } from '../api/body-api';

const WEIGHT_DEFAULTS = {
  date: new Date().toISOString().split('T')[0],
  weight_kg: undefined,
  body_fat_pct: undefined,
  muscle_mass_pct: undefined,
  muscle_mass_kg: undefined,
  body_water_pct: undefined,
  bone_mass_kg: undefined,
  visceral_fat: undefined,
  bmr: undefined,
  notes: null,
  neck_cm: undefined,
  chest_cm: undefined,
  waist_cm: undefined,
  hips_cm: undefined,
  bicep_r_cm: undefined,
  bicep_l_cm: undefined,
  thigh_r_cm: undefined,
  thigh_l_cm: undefined,
  calf_r_cm: undefined,
  calf_l_cm: undefined,
};

/**
 * Hook to manage Weight Tab state and logic
 */
export function useWeightTab() {
  const [stats, setStats] = useState<BodyCompositionStats | null>(null);
  const [history, setHistory] = useState<WeightLog[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [editingDate, setEditingDate] = useState<string | null>(null);
  const notify = useNotificationStore();
  const { t } = useTranslation();
  const muscleMassShort = t('body.weight.muscle_mass').split(' ')[0];

  const mandatoryNumberSchema = (min: number, max: number, label: string) => z.preprocess(
    (val) => (val === "" || val === null || val === undefined || (typeof val === 'number' && isNaN(val))) ? undefined : Number(val),
    z.number({ 
      required_error: t('validation.field_required', { field: label }),
      invalid_type_error: t('validation.invalid_type_number', { field: label })
    })
    .min(min, t('validation.number_min', { field: label, min }))
    .max(max, t('validation.number_max', { field: label, max }))
  );

  const optionalNumberSchema = (min: number, max: number, label: string) => z.preprocess(
    (val) => (val === "" || val === null || val === undefined || (typeof val === 'number' && isNaN(val))) ? undefined : Number(val),
    z.number({ 
      invalid_type_error: t('validation.invalid_type_number', { field: label })
    })
    .min(min, t('validation.number_min', { field: label, min }))
    .max(max, t('validation.number_max', { field: label, max }))
    .optional()
    .nullable()
  );

  const weightSchema = z.object({
    date: z.string().min(1, t('validation.field_required', { field: t('body.nutrition.date') })),
    weight_kg: mandatoryNumberSchema(30, 300, t('body.weight.weight').split(' ')[0] ?? ''),
    body_fat_pct: mandatoryNumberSchema(2, 100, t('body.weight.body_fat').split(' ')[0] ?? ''),
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    muscle_mass_pct: optionalNumberSchema(2, 100, `${muscleMassShort!} (%)`),
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    muscle_mass_kg: optionalNumberSchema(10, 200, `${muscleMassShort!} (kg)`),
    body_water_pct: optionalNumberSchema(2, 100, t('body.weight.body_water').split(' ')[0] ?? ''),
    bone_mass_kg: optionalNumberSchema(0, 20, t('body.weight.bone_mass').split(' ')[0] ?? ''),
    visceral_fat: optionalNumberSchema(0, 50, t('body.weight.visceral_fat').split(' ')[0] ?? ''),
    bmr: optionalNumberSchema(500, 5000, t('body.weight.bmr').split(' ')[0] ?? ''),
    notes: z.string().max(500, t('validation.max_chars', { max: 500 })).optional().nullable(),
    // Measurements
    neck_cm: optionalNumberSchema(20, 100, t('body.weight.neck')),
    chest_cm: optionalNumberSchema(40, 200, t('body.weight.chest')),
    waist_cm: optionalNumberSchema(40, 200, t('body.weight.waist')),
    hips_cm: optionalNumberSchema(40, 200, t('body.weight.hips')),
    bicep_r_cm: optionalNumberSchema(10, 100, t('body.weight.bicep_r')),
    bicep_l_cm: optionalNumberSchema(10, 100, t('body.weight.bicep_l')),
    thigh_r_cm: optionalNumberSchema(20, 150, t('body.weight.thigh_r')),
    thigh_l_cm: optionalNumberSchema(20, 150, t('body.weight.thigh_l')),
    calf_r_cm: optionalNumberSchema(10, 100, t('body.weight.calf_r')),
    calf_l_cm: optionalNumberSchema(10, 100, t('body.weight.calf_l')),
  });

  type WeightFormData = z.infer<typeof weightSchema>;

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors }
  } = useForm<WeightFormData>({
    resolver: zodResolver(weightSchema),
    defaultValues: WEIGHT_DEFAULTS,
  });

  const loadData = useCallback(async (targetPage = 1) => {
    setIsLoading(true);
    try {
      const [statsRes, historyRes] = await Promise.all([
        bodyApi.getBodyCompositionStats(),
        bodyApi.getWeightHistory(targetPage)
      ]);
      setStats(statsRes);
      setHistory(historyRes.logs);
      setPage(historyRes.page);
      setTotalPages(historyRes.total_pages);
    } catch (error) {
      // Just notify once.
      console.error(error);
      notify.error(t('body.weight.notifications.load_error'));
    } finally {
      setIsLoading(false);
    }
  }, [notify, t]);

  // Initial load
  useEffect(() => {
    void loadData();
  }, [loadData]);

  const changePage = (newPage: number) => {
    void loadData(newPage);
  };

  const onSubmit = async (data: WeightFormData) => {
    setIsSaving(true);
    try {
      // Clean up null values for API
      const payload = Object.fromEntries(
        Object.entries(data).filter(([_, v]) => v !== null)
      );
      
      await bodyApi.logWeight(data.weight_kg, payload as Partial<WeightLog>);
      notify.success(t('body.weight.notifications.save_success'));
      setEditingDate(null);
      reset({ ...WEIGHT_DEFAULTS, date: new Date().toISOString().split('T')[0] });
      await loadData(1); // Reload first page on new entry
    } catch {
      notify.error(t('body.weight.notifications.save_error'));
    } finally {
      setIsSaving(false);
    }
  };

  const deleteEntry = async (date: string) => {
    try {
      await bodyApi.deleteWeight(date);
      notify.success(t('body.weight.notifications.delete_success'));
      await loadData(page); // Reload current page
    } catch {
      notify.error(t('body.weight.notifications.delete_error'));
    }
  };

  const cancelEdit = () => {
    setEditingDate(null);
    reset({ ...WEIGHT_DEFAULTS, date: new Date().toISOString().split('T')[0] });
  };

  const editEntry = (log: WeightLog) => {
    setEditingDate(log.date);
    reset({
      date: log.date,
      weight_kg: log.weight_kg,
      body_fat_pct: log.body_fat_pct ?? undefined,
      muscle_mass_pct: log.muscle_mass_pct ?? undefined,
      muscle_mass_kg: log.muscle_mass_kg ?? undefined,
      body_water_pct: log.body_water_pct ?? undefined,
      bone_mass_kg: log.bone_mass_kg ?? undefined,
      visceral_fat: log.visceral_fat ?? undefined,
      bmr: log.bmr ?? undefined,
      notes: log.notes ?? null,
      neck_cm: log.neck_cm ?? undefined,
      chest_cm: log.chest_cm ?? undefined,
      waist_cm: log.waist_cm ?? undefined,
      hips_cm: log.hips_cm ?? undefined,
      bicep_r_cm: log.bicep_r_cm ?? undefined,
      bicep_l_cm: log.bicep_l_cm ?? undefined,
      thigh_r_cm: log.thigh_r_cm ?? undefined,
      thigh_l_cm: log.thigh_l_cm ?? undefined,
      calf_r_cm: log.calf_r_cm ?? undefined,
      calf_l_cm: log.calf_l_cm ?? undefined,
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return {
    stats,
    history,
    isLoading,
    isSaving,
    page,
    totalPages,
    changePage,
    register,
    handleSubmit: handleSubmit(onSubmit),
    control,
    errors,
    loadData,
    deleteEntry,
    editEntry,
    cancelEdit,
    isEditing: editingDate !== null,
    editingDate,
  };
}
