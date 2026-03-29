import { History, Scale, Plus } from 'lucide-react';
import { useEffect, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';

import { DataView } from '../../../shared/components/ui/premium/DataView';
import { Pagination } from '../../../shared/components/ui/premium/Pagination';
import { ViewHeader } from '../../../shared/components/ui/premium/ViewHeader';
import { Skeleton } from '../../../shared/components/ui/Skeleton';
import { useBodyStore } from '../../../shared/hooks/useBody';
import { useDemoMode } from '../../../shared/hooks/useDemoMode';
import type { WeightLog, WeightLogFormData } from '../../../shared/types/body';

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
    error,
    fetchLogs,
    fetchStats,
    deleteLog,
    logWeight,
  } = useBodyStore();
  
  const { t } = useTranslation();
  const { isReadOnly, blockIfReadOnly } = useDemoMode();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [selectedLog, setSelectedLog] = useState<WeightLog | null>(null);

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
    setIsDrawerOpen(false);
    setSelectedLog(null);
  }, []);

  const onSave = async (data: WeightLogFormData) => {
    if (blockIfReadOnly()) {
      return;
    }
    try {
      await logWeight(data as Partial<WeightLog>);
      handleCloseDrawer();
    } catch { /* Handled by store */ }
  };

  const onRetry = () => {
    void fetchLogs();
    void fetchStats();
  };

  const onDelete = (date: string) => {
    if (blockIfReadOnly()) {
      return;
    }
    void deleteLog(date);
  };

  const loadingSkeleton = (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-pulse">
      {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-32 rounded-3xl bg-white/5" />)}
    </div>
  );

  return (
    <div className="space-y-10">
      
      {/* HEADER SECTION */}
      <ViewHeader 
        title={t('body.weight.history_title')}
        subtitle={t('body.weight_subtitle')}
        icon={<Scale size={20} className="text-emerald-500" />}
        action={{
          label: t('body.weight.register_weight'),
          icon: <Plus size={20} strokeWidth={3} />,
          onClick: handleRegisterWeight,
          disabled: isReadOnly,
        }}
        className="px-2"
      />

      {/* DATA ORCHESTRATION LAYER */}
      <DataView 
        isLoading={isLoading && logs.length === 0}
        error={error}
        isEmpty={logs.length === 0}
        onRetry={onRetry}
        loadingSkeleton={loadingSkeleton}
        emptyState={{
          title: t('body.weight.empty_history'),
          icon: <History size={40} className="text-zinc-500" />
        }}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {logs.map(log => (
            <WeightLogCard 
              key={log.id ?? log.date} 
              log={log} 
              isReadOnly={isReadOnly}
              onDelete={onDelete} 
              onEdit={handleEditWeight}
              onClick={handleViewDrawer}
            />
          ))}
        </div>

        {/* PAGINATION - Standardized */}
        <Pagination 
          currentPage={1} 
          totalPages={1} 
          onPageChange={() => { /* Not implemented in body store yet */ }} 
          isLoading={isLoading}
        />
      </DataView>

      <WeightLogDrawer 
        log={selectedLog}
        isOpen={isDrawerOpen} 
        isReadOnly={isReadOnly}
        onClose={handleCloseDrawer} 
        onSubmit={onSave}
      />
    </div>
  );
}
