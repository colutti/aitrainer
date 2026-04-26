import { History } from 'lucide-react';
import { useEffect, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';

import { Button } from '../../../shared/components/ui/Button';
import { DataList } from '../../../shared/components/ui/DataList';
import { useBodyStore } from '../../../shared/hooks/useBody';
import { useConfirmation } from '../../../shared/hooks/useConfirmation';
import { useDemoMode } from '../../../shared/hooks/useDemoMode';
import { PREMIUM_UI } from '../../../shared/styles/ui-variants';
import type { WeightLog, WeightLogFormData } from '../../../shared/types/body';
import { cn } from '../../../shared/utils/cn';

import { WeightLogCard } from './WeightLogCard';
import { WeightLogDrawer } from './WeightLogDrawer';

/**
 * WeightTab component
 * 
 * Refactored to use DataView orchestrator and shared Premium components.
 */
export function WeightTab() {
  const {
    logs,
    isLoading,
    page,
    totalPages,
    fetchLogs,
    fetchStats,
    deleteLog,
    logWeight,
  } = useBodyStore();
  
  const { t } = useTranslation();
  const { isReadOnly, blockIfReadOnly } = useDemoMode();
  const { confirm } = useConfirmation();
  const [searchParams, setSearchParams] = useSearchParams();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [selectedLog, setSelectedLog] = useState<WeightLog | null>(null);
  const shouldAutoOpenDrawer = !isReadOnly && searchParams.get('action') === 'log-weight';

  useEffect(() => {
    void fetchLogs();
    void fetchStats();
  }, [fetchLogs, fetchStats]);

  const handleViewDrawer = useCallback((log?: WeightLog) => {
    // eslint-disable-next-line @typescript-eslint/prefer-nullish-coalescing
    setSelectedLog(log || null);
    setIsDrawerOpen(true);
  }, []);

  const handleRegisterWeight = useCallback(() => {
    if (blockIfReadOnly()) {
      return;
    }
    handleViewDrawer();
  }, [blockIfReadOnly, handleViewDrawer]);

  const handleEditWeight = useCallback((log: WeightLog) => {
    if (blockIfReadOnly()) {
      return;
    }
    handleViewDrawer(log);
  }, [blockIfReadOnly, handleViewDrawer]);

  const handleCloseDrawer = useCallback(() => {
    if (searchParams.get('action') === 'log-weight') {
      const nextParams = new URLSearchParams(searchParams);
      nextParams.delete('action');
      setSearchParams(nextParams, { replace: true });
    }
    setIsDrawerOpen(false);
    setSelectedLog(null);
  }, [searchParams, setSearchParams]);

  const onSave = async (data: WeightLogFormData) => {
    if (blockIfReadOnly()) {
      return;
    }
    try {
      await logWeight(data as Partial<WeightLog>);
      handleCloseDrawer();
    } catch { /* Handled by store */ }
  };

  const onPageChange = (newPage: number) => {
    void fetchLogs(newPage);
  };

  const onDelete = async (date: string) => {
    if (blockIfReadOnly()) {
      return;
    }
    const isConfirmed = await confirm({
      title: t('body.weight.delete_confirm_title'),
      message: t('body.weight.delete_confirm_message'),
      confirmText: t('body.weight.delete_confirm_btn'),
      type: 'danger',
    });
    if (isConfirmed) {
      void deleteLog(date);
    }
  };

  return (
    <div className="space-y-10">
      {/* DATA ORCHESTRATION LAYER */}
      <DataList
        data={logs}
        actions={logs.length > 0 ? (
          <Button
            type="button"
            fullWidth
            onClick={handleRegisterWeight}
            disabled={isReadOnly}
            className={cn(PREMIUM_UI.button.premium, "w-full md:w-auto px-5")}
          >
            {t('body.weight.register_weight')}
          </Button>
        ) : undefined}
        renderItem={(log) => (
          <WeightLogCard
            log={log}
            isReadOnly={isReadOnly}
            onDelete={(date) => { void onDelete(date); }}
            onEdit={handleEditWeight}
            onClick={handleViewDrawer}
          />
        )}
        keyExtractor={(log) => log.id ?? log.date}
        isLoading={isLoading}
        layout="list"
        emptyState={{
          title: t('body.weight.empty_history'),
          description: t('body.weight.empty_history_desc', ''),
          icon: <History size={40} className="text-zinc-500" />,
          action: (
            <Button
              type="button"
              onClick={handleRegisterWeight}
              disabled={isReadOnly}
              className={cn(PREMIUM_UI.button.premium, "w-full px-5")}
            >
              {t('body.weight.register_weight')}
            </Button>
          ),
        }}
        pagination={{
          currentPage: page,
          totalPages,
          onPageChange,
        }}
        className="space-y-8"
        gridClassName="grid-cols-1"
      />

      <WeightLogDrawer 
        log={selectedLog}
        isOpen={isDrawerOpen || shouldAutoOpenDrawer} 
        isReadOnly={isReadOnly}
        onClose={handleCloseDrawer} 
        onSubmit={onSave}
      />
    </div>
  );
}
