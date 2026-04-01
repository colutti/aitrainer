import { History } from 'lucide-react';
import { useEffect, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';

import { Button } from '../../../shared/components/ui/Button';
import { DataList } from '../../../shared/components/ui/DataList';
import { useDemoMode } from '../../../shared/hooks/useDemoMode';
import { useNutritionStore } from '../../../shared/hooks/useNutrition';
import { PREMIUM_UI } from '../../../shared/styles/ui-variants';
import { type NutritionLog, type NutritionFormData } from '../../../shared/types/nutrition';
import { cn } from '../../../shared/utils/cn';
import { NutritionLogCard } from '../../nutrition/components/NutritionLogCard';

import { NutritionLogDrawer } from './NutritionLogDrawer';

/**
 * NutritionTab component
 * 
 * Refactored to use DataView orchestrator and reusable UI components.
 */
export function NutritionTab() {
  const {
    logs,
    isLoading,
    page,
    totalPages,
    fetchLogs,
    fetchStats,
    deleteLog,
    createLog,
  } = useNutritionStore();
  
  const { t } = useTranslation();
  const { isReadOnly, blockIfReadOnly } = useDemoMode();

  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [selectedLog, setSelectedLog] = useState<NutritionLog | null>(null);
  const [drawerMode, setDrawerMode] = useState<'view' | 'edit'>('view');

  useEffect(() => {
    void fetchLogs();
    void fetchStats();
  }, [fetchLogs, fetchStats]);

  const handleOpenDrawer = useCallback((log: NutritionLog | null, mode: 'view' | 'edit') => {
    setSelectedLog(log);
    setDrawerMode(mode);
    setIsDrawerOpen(true);
  }, []);

  const handleCloseDrawer = useCallback(() => {
    setIsDrawerOpen(false);
    setSelectedLog(null);
  }, []);

  const onSave = async (data: NutritionFormData) => {
    if (blockIfReadOnly()) return;
    
    try {
      await createLog({
        date: data.date,
        source: data.source,
        calories: data.calories,
        protein_grams: data.protein_grams ?? 0,
        carbs_grams: data.carbs_grams ?? 0,
        fat_grams: data.fat_grams ?? 0,
      });
      handleCloseDrawer();
    } catch {
      // Handled by store
    }
  };

  const onDelete = (id: string) => {
    if (blockIfReadOnly()) {
      return;
    }
    void deleteLog(id);
  };

  const onPageChange = (p: number) => {
    void fetchLogs(p);
  };

  return (
    <div className="space-y-10">
      {/* DATA ORCHESTRATION LAYER */}
      <DataList
        data={logs}
        actions={(
          <div className="w-full">
              <Button
                type="button"
                fullWidth
                onClick={() => { handleOpenDrawer(null, 'edit'); }}
                disabled={isReadOnly}
                className={cn(PREMIUM_UI.button.premium, "w-full md:w-auto px-5")}
              >
                {t('nutrition.register_meal')}
              </Button>
          </div>
        )}
        renderItem={(log) => (
          <NutritionLogCard
            log={log}
            isReadOnly={isReadOnly}
            onDelete={onDelete}
            onEdit={(l) => { handleOpenDrawer(l, 'edit'); }}
            onClick={(l) => { handleOpenDrawer(l, 'view'); }}
          />
        )}
        keyExtractor={(log) => log.id}
        isLoading={isLoading}
        layout="grid"
        emptyState={{
          title: t('nutrition.empty_history_title'),
          description: '',
          icon: <History size={40} className="text-zinc-500" />
        }}
        pagination={{
          currentPage: page,
          totalPages,
          onPageChange,
        }}
        className="space-y-8"
        gridClassName="grid-cols-1 md:grid-cols-2"
      />

      <NutritionLogDrawer
        log={selectedLog}
        isOpen={isDrawerOpen}
        onClose={handleCloseDrawer}
        onSubmit={onSave}
        mode={drawerMode}
        isReadOnly={isReadOnly}
      />
    </div>
  );
}
