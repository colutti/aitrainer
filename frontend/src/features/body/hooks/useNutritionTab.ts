import { zodResolver } from '@hookform/resolvers/zod';
import { useState, useCallback, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { useNotificationStore } from '../../../shared/hooks/useNotification';
import type { NutritionLog, NutritionStats } from '../../../shared/types/nutrition';
import { bodyApi } from '../api/body-api';

const mandatoryNumberSchema = (min: number, max: number, label: string) => z.preprocess(
  (val) => (val === "" || val === null || (typeof val === 'number' && isNaN(val))) ? undefined : Number(val),
  z.number({ 
    required_error: `${label} é obrigatório`,
    invalid_type_error: `O ${label} deve ser um número` 
  })
  .min(min, `${label} deve ser ao menos ${min.toString()}`)
  .max(max, `${label} deve ser no máximo ${max.toString()}`)
);

const optionalNumberSchema = (min: number, max: number, label: string) => z.preprocess(
  (val) => (val === "" || val === null || (typeof val === 'number' && isNaN(val))) ? undefined : Number(val),
  z.number({ 
    invalid_type_error: `O ${label} deve ser um número` 
  })
  .min(min, `${label} deve ser ao menos ${min.toString()}`)
  .max(max, `${label} deve ser no máximo ${max.toString()}`)
  .optional()
  .nullable()
);

const nutritionSchema = z.object({
  date: z.string().min(1, "A data é obrigatória"),
  source: z.string().min(1),
  calories: mandatoryNumberSchema(0, 10000, "Calorias"),
  protein_grams: optionalNumberSchema(0, 1000, "Proteína"),
  carbs_grams: optionalNumberSchema(0, 2000, "Carboidrato"),
  fat_grams: optionalNumberSchema(0, 500, "Gordura"),
});

type NutritionFormData = z.infer<typeof nutritionSchema>;

const NUTRITION_DEFAULTS = {
  date: new Date().toISOString().split('T')[0],
  source: 'Manual',
  calories: undefined,
  protein_grams: undefined,
  carbs_grams: undefined,
  fat_grams: undefined,
};

/**
 * Hook to manage Nutrition Tab state and logic
 */
export function useNutritionTab() {
  const [logs, setLogs] = useState<NutritionLog[]>([]);
  const [stats, setStats] = useState<NutritionStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [daysFilter, setDaysFilter] = useState<number | undefined>(undefined);
  const [editingId, setEditingId] = useState<string | null>(null);

  const notify = useNotificationStore();

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors }
  } = useForm<NutritionFormData>({
    resolver: zodResolver(nutritionSchema),
    defaultValues: NUTRITION_DEFAULTS,
  });

  const loadLogs = useCallback(async (page = 1, filter = daysFilter) => {
    try {
      const res = await bodyApi.getNutritionLogs(page, 10, filter);
      setLogs(res.logs);
      setTotalPages(res.total_pages);
      setCurrentPage(res.page);
    } catch {
      notify.error('Erro ao carregar logs nutricionais.');
    }
  }, [daysFilter, notify]);

  const loadStats = useCallback(async () => {
    try {
      const statsRes = await bodyApi.getNutritionStats();
      setStats(statsRes);
    } catch {
      notify.error('Erro ao carregar estatísticas nutricionais.');
    }
  }, [notify]);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    await Promise.all([loadStats(), loadLogs(1)]);
    setIsLoading(false);
  }, [loadStats, loadLogs]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const onSubmit = async (data: NutritionFormData) => {
    setIsSaving(true);
    try {
      const payload = Object.fromEntries(
        Object.entries(data).filter(([_, v]) => v !== null)
      );
      await bodyApi.logNutrition(payload as Partial<NutritionLog>);
      notify.success('Registro nutricional salvo!');
      setEditingId(null);
      reset({ ...NUTRITION_DEFAULTS, date: new Date().toISOString().split('T')[0] });
      await loadData();
    } catch {
      notify.error('Erro ao salvar registro nutricional.');
    } finally {
      setIsSaving(false);
    }
  };

  const deleteEntry = async (id: string) => {
    try {
      await bodyApi.deleteNutritionLog(id);
      notify.success('Registro removido.');
      await loadData();
    } catch {
      notify.error('Erro ao remover registro.');
    }
  };

  const cancelEdit = () => {
    setEditingId(null);
    reset({ ...NUTRITION_DEFAULTS, date: new Date().toISOString().split('T')[0] });
  };

  const editEntry = (log: NutritionLog) => {
    // Extract date safely: avoid UTC conversion by slicing the string directly
    const dateStr = typeof log.date === 'string'
      ? log.date.split('T')[0]
      : new Date(log.date as unknown as string).toISOString().split('T')[0];

    setEditingId(log.id);
    reset({
      date: dateStr,
      source: log.source,
      calories: log.calories,
      protein_grams: log.protein_grams,
      carbs_grams: log.carbs_grams,
      fat_grams: log.fat_grams,
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const setFilter = (days: number | undefined) => {
    setDaysFilter(days);
    void loadLogs(1, days);
  };

  const nextPage = () => {
    if (currentPage < totalPages) {
      void loadLogs(currentPage + 1);
    }
  };

  const prevPage = () => {
    if (currentPage > 1) {
      void loadLogs(currentPage - 1);
    }
  };

  const changePage = (page: number) => {
    void loadLogs(page);
  };

  return {
    logs,
    stats,
    isLoading,
    isSaving,
    currentPage,
    totalPages,
    daysFilter,
    register,
    handleSubmit: handleSubmit(onSubmit),
    control,
    errors,
    loadData,
    deleteEntry,
    editEntry,
    cancelEdit,
    isEditing: editingId !== null,
    editingId,
    setFilter,
    nextPage,
    prevPage,
    changePage
  };
}
