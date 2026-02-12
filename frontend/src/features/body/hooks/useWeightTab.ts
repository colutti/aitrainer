import { zodResolver } from '@hookform/resolvers/zod';
import { useState, useCallback, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { useNotificationStore } from '../../../shared/hooks/useNotification';
import type { WeightLog, BodyCompositionStats } from '../../../shared/types/body';
import { bodyApi } from '../api/body-api';

const mandatoryNumberSchema = (min: number, max: number, label: string) => z.preprocess(
  (val) => (val === "" || val === null || val === undefined || (typeof val === 'number' && isNaN(val))) ? undefined : Number(val),
  z.number({ 
    required_error: `${label} é obrigatório`,
    invalid_type_error: `O ${label} deve ser um número` 
  })
  .min(min, `${label} deve ser ao menos ${min.toString()}`)
  .max(max, `${label} deve ser no máximo ${max.toString()}`)
);

const optionalNumberSchema = (min: number, max: number, label: string) => z.preprocess(
  (val) => (val === "" || val === null || val === undefined || (typeof val === 'number' && isNaN(val))) ? undefined : Number(val),
  z.number({ 
    invalid_type_error: `O ${label} deve ser um número` 
  })
  .min(min, `${label} deve ser ao menos ${min.toString()}`)
  .max(max, `${label} deve ser no máximo ${max.toString()}`)
  .optional()
  .nullable()
);

const weightSchema = z.object({
  date: z.string().min(1, "A data é obrigatória"),
  weight_kg: mandatoryNumberSchema(30, 300, "Peso"),
  body_fat_pct: mandatoryNumberSchema(2, 100, "Gordura corporal"),
  muscle_mass_pct: optionalNumberSchema(2, 100, "Massa muscular (%)"),
  muscle_mass_kg: optionalNumberSchema(10, 200, "Massa muscular (kg)"),
  body_water_pct: optionalNumberSchema(2, 100, "Água corporal"),
  bone_mass_kg: optionalNumberSchema(0, 20, "Massa óssea"),
  visceral_fat: optionalNumberSchema(0, 50, "Gordura visceral"),
  bmr: optionalNumberSchema(500, 5000, "TMB"),
  notes: z.string().max(500, "Máximo de 500 caracteres").optional().nullable(),
  // Measurements
  neck_cm: optionalNumberSchema(20, 100, "Pescoço"),
  chest_cm: optionalNumberSchema(40, 200, "Peito"),
  waist_cm: optionalNumberSchema(40, 200, "Cintura"),
  hips_cm: optionalNumberSchema(40, 200, "Quadril"),
  bicep_r_cm: optionalNumberSchema(10, 100, "Bíceps (D)"),
  bicep_l_cm: optionalNumberSchema(10, 100, "Bíceps (E)"),
  thigh_r_cm: optionalNumberSchema(20, 150, "Coxa (D)"),
  thigh_l_cm: optionalNumberSchema(20, 150, "Coxa (E)"),
  calf_r_cm: optionalNumberSchema(10, 100, "Panturrilha (D)"),
  calf_l_cm: optionalNumberSchema(10, 100, "Panturrilha (E)"),
});

type WeightFormData = z.infer<typeof weightSchema>;

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
  const notify = useNotificationStore();

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors }
  } = useForm<WeightFormData>({
    resolver: zodResolver(weightSchema),
    defaultValues: {
      date: new Date().toISOString().split('T')[0],
      weight_kg: undefined,
    }
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
    } catch (_error) {
      console.error('Failed to load weight data:', _error);
      // Only notify if not already loading (which we set to true above, but meaningful for retries)
      // Actually, create a toast ID to prevent duplicates if needed, but simpler:
      // Just notify once.
      notify.error('Erro ao carregar dados de peso.');
    } finally {
      setIsLoading(false);
    }
  }, [notify]);

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
      notify.success('Registro de peso salvo!');
      reset({
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
        calf_l_cm: undefined
      });
      await loadData(1); // Reload first page on new entry
    } catch {
      notify.error('Erro ao salvar registro de peso.');
    } finally {
      setIsSaving(false);
    }
  };

  const deleteEntry = async (date: string) => {
    try {
      await bodyApi.deleteWeight(date);
      notify.success('Registro removido.');
      await loadData(page); // Reload current page
    } catch {
      notify.error('Erro ao remover registro.');
    }
  };

  const editEntry = (log: WeightLog) => {
    setValue('date', log.date);
    setValue('weight_kg', log.weight_kg);
    setValue('body_fat_pct', log.body_fat_pct ?? 0);
    setValue('muscle_mass_pct', log.muscle_mass_pct ?? undefined);
    setValue('muscle_mass_kg', log.muscle_mass_kg ?? undefined);
    setValue('body_water_pct', log.body_water_pct ?? undefined);
    setValue('bone_mass_kg', log.bone_mass_kg ?? undefined);
    setValue('visceral_fat', log.visceral_fat ?? undefined);
    setValue('bmr', log.bmr ?? undefined);
    setValue('notes', log.notes ?? null);
    setValue('neck_cm', log.neck_cm ?? undefined);
    setValue('chest_cm', log.chest_cm ?? undefined);
    setValue('waist_cm', log.waist_cm ?? undefined);
    setValue('hips_cm', log.hips_cm ?? undefined);
    setValue('bicep_r_cm', log.bicep_r_cm ?? undefined);
    setValue('bicep_l_cm', log.bicep_l_cm ?? undefined);
    setValue('thigh_r_cm', log.thigh_r_cm ?? undefined);
    setValue('thigh_l_cm', log.thigh_l_cm ?? undefined);
    setValue('calf_r_cm', log.calf_r_cm ?? undefined);
    setValue('calf_l_cm', log.calf_l_cm ?? undefined);
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
    errors,
    loadData,
    deleteEntry,
    editEntry
  };
}
