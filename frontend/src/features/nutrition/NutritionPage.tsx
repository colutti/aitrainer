import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';

import { useConfirmation } from '../../shared/hooks/useConfirmation';
import { useNotificationStore } from '../../shared/hooks/useNotification';
import { useNutritionStore } from '../../shared/hooks/useNutrition';

import { NutritionView } from './components/NutritionView';

/**
 * NutritionPage component (Container)
 * 
 * Manages nutrition data fetching, logic and state.
 * Delegates rendering to the NutritionView presenter.
 */
export default function NutritionPage() {
  const { 
    logs, 
    stats, 
    isLoading, 
    fetchLogs, 
    fetchStats, 
    deleteLog,
    page,
    totalPages
  } = useNutritionStore();
  
  const { confirm } = useConfirmation();
  const notify = useNotificationStore();
  const { t } = useTranslation();

  useEffect(() => {
    void fetchLogs();
    void fetchStats();
  }, [fetchLogs, fetchStats]);

  const handleDelete = async (id: string) => {
    const isConfirmed = await confirm({
      title: t('nutrition.delete_confirm_title'),
      message: t('nutrition.delete_confirm_message'),
      confirmText: t('nutrition.delete_confirm_btn'),
      type: 'danger',
    });

    if (isConfirmed) {
      try {
        await deleteLog(id);
        notify.success(t('nutrition.delete_success'));
      } catch {
        notify.error(t('nutrition.delete_error'));
      }
    }
  };

  return (
    <NutritionView 
      logs={logs}
      stats={stats}
      isLoading={isLoading}
      onRegisterMeal={() => {
        // Lógica de abertura do drawer de registro (TODO na próxima task)
        notify.info("Registro manual em breve nesta UI Premium");
      }}
      onImport={() => {
        notify.info("Importação em breve nesta UI Premium");
      }}
      onDeleteLog={(id) => { void handleDelete(id); }}
      pagination={{
        currentPage: page,
        totalPages: totalPages,
        onPageChange: (newPage) => { void fetchLogs(newPage); }
      }}
    />
  );
}
